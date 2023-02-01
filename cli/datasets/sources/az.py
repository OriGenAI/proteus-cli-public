import re
import uuid

# from azure.storage.blob._models import BlobProperties as AzureBlobProperties
from io import BytesIO

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient, BlobClient, BlobBlock

from cli.config import config
from .common import Source, SourcedItem
from ... import proteus

CONTENT_CHUNK_SIZE = 10 * 1024 * 1024


class AZSource(Source):
    URI_re = re.compile(
        r"^https:\/\/(?P<bucket_name>.*\.windows\.net)\/" r"(?P<container_name>[^\/]*)(\/)?(?P<prefix>.*)?$"
    )

    @proteus.may_insist_up_to(5, 1)
    def list_contents(self, starts_with="", ends_with=None):
        bucket_uri = self.uri
        match = self.URI_re.match(bucket_uri.rstrip("/"))
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
                yield SourcedItem(item, item_name, self, item.size)

    def open(self, reference):
        reference_path = reference.get("name")
        file_size = reference["size"]
        modified = reference["last_modified"]
        blob_client = self._client(reference)

        stream = BytesIO()
        streamdownloader = blob_client.download_blob(max_concurrency=4)
        streamdownloader.download_to_stream(stream)
        stream.seek(0)
        return reference_path, file_size, modified, stream

    def _client(self, reference):
        container = reference.get("container")
        reference_path = reference.get("name")

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

        return blob_client

    @proteus.may_insist_up_to(5, 1)
    def _download_blob(self, reference):
        return self._client(reference).download_blob(max_concurrency=3, read_timeout=8000, timeout=8000)

    def download(self, reference):
        return self._download_blob(reference).readall()

    def chunks(self, reference):
        client = self._client(reference)
        with AZObjectFile(client, mode="r", size=reference.size) as f:
            for chunk in f:
                yield chunk


class AZObjectFile:
    """An ObjectFile in object storage that can be opened and closed.
    See Objects.open()"""

    def __init__(self, client, mode, size):
        """Initialize the Object object with a name and a blob_client
        mode is w or r, size is the blob size.
        """
        self.client = client
        self.block_list = []
        self.mode = mode
        self.__open__ = True
        self.pos = 0
        self.size = size

    def write(self, chunk):
        """Write a chunk of data (a part of the data) into the object"""
        block_id = str(uuid.uuid4())
        self.client.stage_block(block_id=block_id, data=chunk)
        self.block_list.append(BlobBlock(block_id=block_id))
        self.client.commit_block_list(self.block_list)

    def close(self):
        """Finalise the object"""
        if self.mode == "w":
            self.client.commit_block_list(self.block_list)
        self.__open__ = False

    def __del__(self):
        if self.__open__:
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__open__:
            self.close()

    def __iter__(self):
        self.pos = 0

        return self

    @proteus.may_insist_up_to(5, delay_in_secs=1)
    def __next__(self):
        data = BytesIO()
        if self.pos >= self.size:
            raise StopIteration()
        elif self.pos + CONTENT_CHUNK_SIZE > self.size:
            size = self.size - self.pos
        else:
            size = CONTENT_CHUNK_SIZE
        self.client.download_blob(offset=self.pos, length=size).download_to_stream(data, max_concurrency=4)
        self.pos += size
        return data.getvalue()

    def read(self, size=CONTENT_CHUNK_SIZE):
        if size is None:
            return self.client.download_blob().readall()
        else:
            if self.pos >= self.size:
                return ""
            elif self.pos + size > self.size:
                size = self.size - self.pos
            data = BytesIO()
            self.client.download_blob(offset=self.pos, length=size).download_to_stream(data, max_concurrency=4)
            self.pos += size
            return data.getvalue()
