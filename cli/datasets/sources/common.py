import re


class SourcedItem:
    def __init__(self, reference, path, source, size):
        self.source = source
        self.path = path
        self.reference = reference
        self.size = size

    _path_rel = None

    @property
    def path_rel(self):
        if self._path_rel is None:
            self._path_rel = self.source.to_relative(self.path)
        return self._path_rel

    def __iter__(self):
        return iter((self.source, self.path, self.reference, self.size))

    def __str__(self):
        return f"< {self.path}@{self.source} >"


class Source:

    URI_re = re.compile(r"^.*$")

    def __init__(self, uri):
        self.uri = uri

    @classmethod
    def accepts(cls, uri):
        match = cls.URI_re.match(str(uri))
        return True if match is not None else False

    def list_contents(self, *args):
        raise NotImplementedError()

    def open(self, reference):
        raise NotImplementedError()

    def cd(self, subpath):
        raise NotImplementedError()

    def fastcopy(self, reference, destination):
        return False

    def to_relative(self, item: str):
        raise NotImplementedError()

    def dirname(self, item: str):
        raise NotImplementedError()

    def join(self, *items):
        raise NotImplementedError()
