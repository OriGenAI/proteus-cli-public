import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .common import Source, SourcedItem


class LocalSource(Source):

    URI_re = re.compile(r"^.*$")

    def __init__(self, uri, sandbox_uri=None):
        super().__init__(os.path.abspath(os.path.expanduser(uri)))
        self.sandbox_uri = os.path.abspath(sandbox_uri or self.uri)

    @property
    def subpath(self):
        return self.uri

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
                if os.path.isdir(fq_file_path):
                    f_files, f_by_extension = self._list_dir_files(fq_file_path)
                    files.extend(f_files)
                    for ext, files in f_by_extension.items():
                        by_extension.setdefault(ext, []).extend(files)
                else:
                    files.append(fq_file_path)
                    parts = file.split(".")
                    if len(parts) == 2:
                        extension = "." + parts[1]
                        by_extension.setdefault(extension, []).append(fq_file_path)

        return files, by_extension

    def open(self, reference):
        self._check_sandbox(reference)
        stats = reference.stat()
        reference_path = str(reference)
        modified = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)
        file_size = stats.st_size
        return reference_path, file_size, modified, reference.open("rb")

    def fastcopy(self, reference, destination):
        self._check_sandbox(reference)
        try:
            os.symlink(reference, destination)
        except BaseException:
            return False

        return True

    def download(self, reference):
        self._check_sandbox(reference)
        with reference.open("rb") as file:
            return file.read()

    def chunks(self, reference):
        self._check_sandbox(reference)
        # FIXME: no real chunk download
        yield self.download(reference)

    def cd(self, subpath):
        if subpath.startswith("/"):
            self._check_sandbox(subpath)
            return self.__class__(subpath, sandbox_uri=self.sandbox_uri)

        return self.__class__(os.path.normpath(self.join(self.uri, subpath)), sandbox_uri=self.uri)

    def _check_sandbox(self, reference):
        if not os.path.abspath(reference).startswith(self.sandbox_uri):
            raise FileNotFoundError(f"File {reference} is outside sandboxed base dir {self.sandbox_uri}")

    def to_relative(self, item: str):
        base_path = os.path.abspath(self.uri)
        assert item.startswith(base_path)
        return os.path.normpath(item).split(base_path, 1)[1].lstrip(os.path.sep)

    def dirname(self, item: str):
        return os.path.dirname(item)

    def join(self, *items):
        return os.path.join(*items)
