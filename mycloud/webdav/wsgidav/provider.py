import inject
import asyncio
from wsgidav.dav_provider import DAVProvider
from mycloud.drive import DriveClient, FileType
from mycloud.webdav.wsgidav.dir_resource import DirResource
from mycloud.webdav.wsgidav.file_resource import FileResource


class MyCloudWebdavProvider(DAVProvider):

    drive_client: DriveClient = inject.attr(DriveClient)

    def get_resource_inst(self, path, environ):
        loop = asyncio.new_event_loop()

        file_type = loop.run_until_complete(
            self.drive_client.get_path_metadata(path))

        if file_type == FileType.Directory:
            return DirResource(path, environ)

        if file_type == FileType.File:
            return FileResource(path, environ)

        return None
