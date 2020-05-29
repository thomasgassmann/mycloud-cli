import inject
from wsgidav.dav_provider import DAVProvider
from mycloud.drive import DriveClient
from mycloud.webdav.wsgidav.dir_resource import DirResource
from mycloud.webdav.wsgidav.file_resource import FileResource


class MyCloudWebdavProvider(DAVProvider):

    drive_client: DriveClient = inject.attr(DriveClient)

    def get_resource_inst(self, path, environ):
        if self.drive_client.is_directory(path):
            return DirResource(path)
