import inject
from wsgidav.dav_provider import DAVProvider
from mycloud.webdav.wsgidav.dir_resource import DirResource
from mycloud.webdav.wsgidav.file_resource import FileResource
from mycloud.webdav.client import MyCloudDavClient, FileType
from mycloud.common import run_sync


class MyCloudWebdavProvider(DAVProvider):

    dav_client: MyCloudDavClient = inject.attr(MyCloudDavClient)

    def get_resource_inst(self, path, environ):
        file_type = self.dav_client.get_file_type(path)

        if file_type == FileType.Dir:
            return DirResource(path, environ)

        if file_type == FileType.File:
            return FileResource(path, environ)

        return None
