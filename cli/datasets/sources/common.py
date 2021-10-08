import re


class Source:

    URI_re = re.compile(r"^.*$")

    def __init__(self, uri):
        self.uri = uri

    @classmethod
    def accepts(cls, uri):
        match = cls.URI_re.match(uri)
        return True if match is not None else False

    def list_contents(self, *args):
        raise NotImplementedError()

    def open(self, reference):
        raise NotImplementedError()


class SourcedItem:
    def __init__(self, reference, path, source):
        self.source = source
        self.path = path
        self.reference = reference

    def __iter__(self):
        return iter((self.source, self.path, self.reference))

    def __str__(self):
        return f"< {self.path}@{self.source} >"
