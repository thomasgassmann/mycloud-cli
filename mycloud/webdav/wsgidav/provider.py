from wsgidav.dav_provider import DAVProvider


class MyCloudWebdavProvider(DAVProvider):

    def get_resource_inst(self, path, environ):
        pass
