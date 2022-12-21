import re

# from azure.storage.blob._models import BlobProperties as AzureBlobProperties
from io import BytesIO

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient, BlobClient
from cli.config import config

from .common import Source, SourcedItem


class AZSource(Source):
    URI_re = re.compile(
        r"^https:\/\/(?P<bucket_name>.*\.windows\.net)\/" r"(?P<container_name>[^\/]*)(\/)?(?P<prefix>.*)?$"
    )

    def list_contents(self, starts_with="", ends_with=None):
        bucket_uri = self.uri
        match = self.URI_re.match(bucket_uri)
        assert match is not None, f"{bucket_uri} must be an s3 URI"
        container_name = match.groupdict()["container_name"]
        prefix = match.groupdict()["prefix"]
        client = ContainerClient.from_connection_string(
            conn_str=config.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container_name,
        )
        for item in client.list_blobs(name_starts_with=prefix + starts_with):
            item_name = item["name"]
            if ends_with is None or item_name.endswith(ends_with):
                yield SourcedItem(item, item_name, self)

    def open(self, reference):
        container = reference.get("container")
        reference_path = reference.get("name")
        file_size = reference["size"]
        modified = reference["last_modified"]
        if config.AZURE_STORAGE_ACCOUNT_URL:
            blob_client = BlobClient(
                config.AZURE_STORAGE_ACCOUNT_URL,
                credential=DefaultAzureCredential(),
                container_name=container,
                blob_name=reference_path,
            )
        elif config.AZURE_STORAGE_CONNECTION_STRING:
            blob_client = BlobClient.from_connection_string(
                conn_str=config.AZURE_STORAGE_CONNECTION_STRING,
                container_name=container,
                blob_name=reference_path,
            )

        stream = BytesIO()
        streamdownloader = blob_client.download_blob(max_concurrency=4)
        streamdownloader.download_to_stream(stream)
        stream.seek(0)
        return reference_path, file_size, modified, stream

    def _download_blob(self, reference):
        container = reference.get("container")
        reference_path = reference.get("name")

        return BlobClient.from_connection_string(
            conn_str=config.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container,
            blob_name=reference_path,
        ).download_blob()

    def download(self, reference):
        return self._download_blob(reference).readall()

    def chunks(self, reference):
        return self._download_blob(reference).chunks()
