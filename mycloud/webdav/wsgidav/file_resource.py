from wsgidav.dav_provider import DAVNonCollection


class FileResource(DAVNonCollection):

    def __init__(self, path, environ):
        super().__init__(path, environ)
