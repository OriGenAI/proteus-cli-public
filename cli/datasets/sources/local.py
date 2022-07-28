import re
from pathlib import Path
from datetime import datetime, timezone
from .common import Source, SourcedItem


class LocalSource(Source):

    URI_re = re.compile(r"^.*$")

    def list_contents(self, starts_with="", ends_with=""):
        source_uri = self.uri

        starts_with = starts_with.lstrip("/")

        for item in Path(source_uri).rglob(f"{starts_with}*{ends_with}"):
            yield SourcedItem(item, str(item), self)

    def open(self, reference):
        stats = reference.stat()
        reference_path = str(reference)
        modified = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)
        file_size = stats.st_size
        return reference_path, file_size, modified, reference.open("rb")

    def download(self, reference):
        with reference.open("rb") as file:
            return file.read()
