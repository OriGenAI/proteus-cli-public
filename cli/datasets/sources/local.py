import os
import re
from datetime import datetime, timezone
from functools import lru_cache
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
            yield SourcedItem(source_uri, str(source_uri), self, lambda: os.path.getsize(str(source_uri)))

        files, by_extension = self._list_dir_files(source_uri)

        if ends_with and ends_with in by_extension:
            for item in by_extension[ends_with]:
                yield SourcedItem(item, str(item), self, lambda: os.path.getsize(str(item)))

        else:
            for item in files:
                if not ends_with or str(item).endswith(ends_with):
                    yield SourcedItem(item, str(item), self, lambda: os.path.getsize(str(item)))

    @lru_cache(maxsize=50000)
    def _list_dir_files(self, source_uri):
        files = []
        by_extension = {}
        if os.path.isdir(source_uri):
            for file in os.listdir(source_uri):
                fq_file_path = Path(os.path.join(source_uri, file))
                files.append(fq_file_path)
                parts = file.split(".")
                if len(parts) == 2:
                    extension = "." + parts[1]
                    by_extension.setdefault(extension, []).append(fq_file_path)

        return files, by_extension

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
