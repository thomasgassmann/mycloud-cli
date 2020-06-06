from pympler import muppy, summary
import pandas as pd
import inject
import asyncio
from wsgidav.dav_provider import DAVProvider
from mycloud.webdav.wsgidav.dir_resource import DirResource
from mycloud.webdav.wsgidav.file_resource import FileResource
from mycloud.webdav.client import MyCloudDavClient, FileType


class MyCloudWebdavProvider(DAVProvider):

    dav_client: MyCloudDavClient = inject.attr(MyCloudDavClient)

    def get_resource_inst(self, path, environ):
        file_type = self.dav_client.get_file_type(path)

        if file_type == FileType.Dir:
            return DirResource(path, environ)

        if file_type == FileType.File:
            return FileResource(path, environ)

        return None
