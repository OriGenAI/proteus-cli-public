import re
from functools import lru_cache
from io import BytesIO

from azure.core.credentials import AzureSasCredential
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient

from cli.config import config
from proteus.bucket import AZ_COPY_PRESENT, AzCopyError
from .common import Source, SourcedItem
from ... import proteus

AZURE_SAS_TOKEN = config.AZURE_SAS_TOKEN

CONTENT_CHUNK_SIZE = 10 * 1024 * 1024


class AZSource(Source):
    URI_re = re.compile(
        r"^https:\/\/(?P<bucket_name>.*\.windows\.net)\/" r"(?P<container_name>[^\/]*)(\/)?(?P<prefix>.*)?$"
    )

    SAS_TOKEN_COMPONENTS = {"sv", "se", "sr", "sp"}

    CLIENT_INIT_PARAMS = {"max_single_get_size": 256 * 1024 * 1024, "max_chunk_get_size": 128 * 1024 * 1024}
    MAX_CONCURRENCY = 10

    def __init__(self, uri, original_uri=None, container_client=None):

        if original_uri:
            (
                self.original_container_name,
                self.original_storage_url,
                self.original_subpath,
                _,
                self.original_uri,
            ) = self._parse_uri(original_uri)
        else:
            self.original_uri = None
            self.original_storage_url = None
            self.original_subpath = None

        self.container_name, self.storage_url, self.subpath, self.url_sas_token, uri = self._parse_uri(uri)

        super().__init__(uri)

        if container_client is not None:
            self.container_client = container_client
        else:
            self._init_container_client()

    def _parse_uri(self, uri):
        match = self.URI_re.match(uri.rstrip("/"))
        assert match is not None, f"{uri} must be a blob storage URI"
        container_name = match.groupdict()["container_name"]
        storage_url = f'https://{match.groupdict()["bucket_name"]}'
        subpath = match.groupdict()["prefix"].split("?")[0].rstrip("/.").rstrip("/")

        uri_parts = iter(uri.split("?"))

        uri = next(uri_parts)
        url_sas_token = next(uri_parts, "")

        return container_name, storage_url, subpath, url_sas_token, uri

    def _init_container_client(self):
        url_sas_token_components = set(x.split("=")[0] for x in self.url_sas_token.split("&") if x)

        errors = []

        if self.SAS_TOKEN_COMPONENTS.intersection(url_sas_token_components) == self.SAS_TOKEN_COMPONENTS:
            self.container_client = ContainerClient.from_container_url(
                f"{self.storage_url}/{self.container_name}?" + self.url_sas_token, **self.CLIENT_INIT_PARAMS
            )
            try:
                next(self.container_client.list_blobs())
                return
            except ClientAuthenticationError as e:
                errors.append(e)

        # Try to see if there is a general SAS token
        if AZURE_SAS_TOKEN:
            self.container_client = ContainerClient(
                self.storage_url,
                credential=AzureSasCredential(AZURE_SAS_TOKEN),
                container_name=self.container_name,
                **self.CLIENT_INIT_PARAMS,
            )

            try:
                next(self.container_client.list_blobs())
                return
            except ClientAuthenticationError as e:
                errors.append(e)

        # Finally try default azure credentials
        auth_methods = [
            "exclude_environment_credential",
            "exclude_cli_credential",
            "exclude_shared_token_cache_credential",
            "exclude_visual_studio_code_credential",
            "exclude_interactive_browser_credential",
            "exclude_powershell_credential",
            "exclude_managed_identity_credential",
        ]

        for auth_method in auth_methods:
            try:
                flags = {auth: True for auth in auth_methods}
                flags[auth_method] = False

                self.container_client = ContainerClient(
                    self.storage_url,
                    credential=DefaultAzureCredential(**flags),
                    container_name=self.container_name,
                    **self.CLIENT_INIT_PARAMS,
                )

                next(self.container_client.list_blobs())

                return
            except ClientAuthenticationError as e:
                errors.append(e)

        for error in errors:
            proteus.logger.error(error)

        raise RuntimeError("Cannot authenticate into azure")

    @proteus.may_insist_up_to(5, 1)
    def list_contents(self, starts_with="", ends_with=None):

        if starts_with:
            subpath = self.join(self.subpath, starts_with)
        else:
            subpath = self.subpath

        original_subpath = self.original_subpath or self.subpath
        # Do not serve files outside the original URI
        if not subpath.startswith(original_subpath.lstrip("/")):
            return

        try:
            for item in self._list_blobs_with_cache(self.container_client, name_starts_with=subpath):
                item_name = f'/{item["name"]}'
                assert item_name.startswith(f"/{subpath}".replace("//", "/"))
                if ends_with is None or item_name.endswith(ends_with):
                    yield SourcedItem(item, item_name, self, item.size)
        except HttpResponseError:
            proteus.logger.error(
                "Missing Azure credentials to perform this operation, please "
                "provide a SAS token or provide another authentication method on Azure"
            )
            raise

    _blob_cache = {}

    @classmethod
    @lru_cache(maxsize=50000)
    def _list_blobs_with_cache(cls, container_client, name_starts_with):
        items = cls._blob_cache.setdefault(container_client, {}).get(name_starts_with)

        # First let's try "indicating" that we want to search in a directory
        # Because maybe we want to search in "SIMULATION_1" but we also have "SIMULATION_10", "SIMULATION_100"...
        if not items:
            items = list(container_client.list_blobs(name_starts_with=name_starts_with + "/"))
            cls._blob_cache[container_client][name_starts_with] = items

        if not items:
            items = list(container_client.list_blobs(name_starts_with=name_starts_with))
            cls._blob_cache[container_client][name_starts_with] = items

        return items

    def open(self, reference):
        reference_path = reference.get("name")
        file_size = reference["size"]
        modified = reference["last_modified"]

        stream = BytesIO()
        streamdownloader = self._download_blob(reference)
        streamdownloader.download_to_stream(stream)
        stream.seek(0)
        return reference_path, file_size, modified, stream

    @proteus.may_insist_up_to(5, 1)
    def _download_blob(self, reference):
        return self.container_client.download_blob(
            reference.get("name"),
            max_concurrency=self.MAX_CONCURRENCY,
            read_timeout=8000,
            timeout=8000,
            length=getattr(reference, "size", None),
            offset=0,
        )

    def download(self, reference):
        return self._download_blob(reference).readall()

    def chunks(self, reference):
        stream = self._download_blob(reference)

        for chunk in stream.chunks():
            yield chunk

    def fastcopy(self, reference, destination):
        if AZ_COPY_PRESENT:
            try:
                download_url = (
                    f'{self.storage_url}/{self.container_name}/{reference.name.strip("/")}?{self.url_sas_token}'
                )
                proteus.bucket.run_azcopy("copy", download_url, destination)
            except AzCopyError as e:
                raise RuntimeError(
                    f'Could not download {reference.name} to {destination} via azcopy: \n{e.out or ""}\n{e.err}'
                )
            return True

        # TODO: Maybe fastcopy can use azcopy?
        return False

    def cd(self, subpath):
        subpath = self.join(self.subpath, subpath)
        uri = f"{self.storage_url}/{self.container_name}{'/' + subpath if subpath else ''}?" + self.url_sas_token

        return self.__class__(uri, container_client=self.container_client, original_uri=self.original_uri or self.uri)

    def to_relative(self, item: str):
        container_path = f'/{self.subpath.strip("/")}/'
        assert item.startswith(container_path)
        return item.split(container_path, 1)[1].lstrip("/")

    def dirname(self, item: str):
        return "/".join(item.split("/")[:-1])

    def join(self, item0, *items):

        item0 = item0.rstrip("/")

        for item in items:
            item = item.rstrip("/")
            for path_part in item.split("/"):
                if path_part == "..":
                    if item0.startswith(".."):
                        item0 += f"/{path_part}"
                    elif not item0:
                        item0 = ".."
                    else:
                        item0 = "/".join(item0.split("/")[:-1])
                else:
                    item0 += f"/{path_part}"

        return item0
