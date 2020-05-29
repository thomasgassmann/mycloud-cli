from wsgidav.dav_provider import DAVCollection


class DirResource(DAVCollection):

    def __init__(self, path, environ):
        super().__init__(path, environ)
