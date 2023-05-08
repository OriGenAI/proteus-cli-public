import os
import re


class Source:

    URI_re = re.compile(r"^.*$")

    def __init__(self, uri):
        self.uri = os.path.abspath(os.path.expanduser(uri))

    @classmethod
    def accepts(cls, uri):
        match = cls.URI_re.match(str(uri))
        return True if match is not None else False

    def list_contents(self, *args):
        raise NotImplementedError()

    def open(self, reference):
        raise NotImplementedError()

    def fastcopy(self, reference, destination):
        return False


class SourcedItem:
    def __init__(self, reference, path, source, size):
        self.source = source
        self.path = path
        self.reference = reference
        self.size = size

    def __iter__(self):
        return iter((self.source, self.path, self.reference, self.size))

    def __str__(self):
        return f"< {self.path}@{self.source} >"
