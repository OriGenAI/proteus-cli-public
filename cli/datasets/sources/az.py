import re
from functools import lru_cache
from io import BytesIO

from azure.core.credentials import AzureSasCredential
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient

from cli.config import config
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

    def __init__(self, uri):
        super().__init__(uri)
        match = self.URI_re.match(uri.rstrip("/"))
        assert match is not None, f"{uri} must be an s3 URI"
        container_name = match.groupdict()["container_name"]
        storage_url = f'https://{match.groupdict()["bucket_name"]}'

        errors = []

        # Check first if the URI include credentials as SAS url
        url_sas_token = next(iter(uri.split("?")[1:]), "")
        url_sas_token_components = set(x.split("=")[0] for x in url_sas_token.split("&") if x)

        if self.SAS_TOKEN_COMPONENTS.intersection(url_sas_token_components) == self.SAS_TOKEN_COMPONENTS:
            self.container_client = ContainerClient.from_container_url(
                f"{storage_url}/{container_name}?" + uri.split("?")[1], **self.CLIENT_INIT_PARAMS
            )
            try:
                next(self.container_client.list_blobs())
                return
            except ClientAuthenticationError as e:
                errors.append(e)

        # Try to see if there is a general SAS token
        if AZURE_SAS_TOKEN:
            self.container_client = ContainerClient(
                storage_url,
                credential=AzureSasCredential(AZURE_SAS_TOKEN),
                container_name=container_name,
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
                    storage_url,
                    credential=DefaultAzureCredential(**flags),
                    container_name=container_name,
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
        bucket_uri = self.uri
        match = self.URI_re.match(bucket_uri.split("?")[0].rstrip("/"))
        assert match is not None, f"{bucket_uri} must be an s3 URI"
        prefix = match.groupdict()["prefix"]
        try:
            for item in self._list_blobs_with_cache(name_starts_with=prefix + starts_with):
                item_name = f'/{item["name"]}'
                assert item_name.startswith(f"/{prefix}{starts_with}".replace("//", "/"))
                if ends_with is None or item_name.endswith(ends_with):
                    yield SourcedItem(item, item_name, self, item.size)
        except HttpResponseError:
            proteus.logger.error(
                "Missing Azure credentials to perform this operation, please "
                "provide a SAS token or provide another authentication method on Azure"
            )
            raise

    _blob_cache = {}

    @lru_cache(maxsize=50000)
    def _list_blobs_with_cache(self, name_starts_with):
        items = self._blob_cache.get(name_starts_with)

        if not items:
            items = list(self.container_client.list_blobs(name_starts_with=name_starts_with))
            self._blob_cache[name_starts_with] = items

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
        # TODO: Maybe fastcopy can use azcopy?
        return False
