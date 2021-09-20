import re
from cli.config import config
from azure.storage.blob import ContainerClient, BlobClient

# from azure.storage.blob._models import BlobProperties as AzureBlobProperties
from io import BytesIO
from .common import Source


class AZSource(Source):
    URI_re = re.compile(
        r"^https://(?P<bucket_name>.*\.windows\.net)/"
        r"(?P<container_name>.*)(/(?P<prefix>.*))?$"
    )

    def list_contents(self):
        bucket_uri = self.uri
        match = self.URI_re.match(bucket_uri)
        assert match is not None, f"{bucket_uri} must be an s3 URI"
        container_name = match.groupdict()["container_name"]
        client = ContainerClient.from_connection_string(
            conn_str=config.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container_name,
        )
        for item in client.list_blobs():
            item.source = self
            yield item, item["name"]

    def open(self, reference):
        container = reference.get("container")
        reference_path = reference.get("name")
        file_size = reference["size"]
        modified = reference["last_modified"]
        blob_client = BlobClient.from_connection_string(
            conn_str=config.AZURE_STORAGE_CONNECTION_STRING,
            container_name=container,
            blob_name=reference_path,
        )
        stream = BytesIO()
        streamdownloader = blob_client.download_blob()
        streamdownloader.download_to_stream(stream)
        stream.seek(0)
        return reference_path, file_size, modified, stream
