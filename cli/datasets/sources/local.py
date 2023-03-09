import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .common import Source, SourcedItem


class LocalSource(Source):

    URI_re = re.compile(r"^.*$")

    def list_contents(self, starts_with="", ends_with=""):
        source_uri = self.uri
        starts_with = starts_with.lstrip("/")
        if starts_with:
            source_uri = os.path.join(source_uri, starts_with)
        source_uri = Path(source_uri)

        if source_uri.exists() and source_uri.is_file():
            yield SourcedItem(source_uri, str(source_uri), self, os.path.getsize(str(source_uri)))

        for item in source_uri.rglob(f"*{ends_with}"):
            yield SourcedItem(item, str(item), self, os.path.getsize(str(item)))

    def open(self, reference):
        stats = reference.stat()
        reference_path = str(reference)
        modified = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)
        file_size = stats.st_size
        return reference_path, file_size, modified, reference.open("rb")

    def fastcopy(self, reference, destination):
        try:
            os.symlink(reference, destination)
        except BaseException:
            return False

        return True

    def download(self, reference):
        with reference.open("rb") as file:
            return file.read()

    def chunks(self, reference):
        # FIXME: no real chunk download
        yield self.download(reference)
