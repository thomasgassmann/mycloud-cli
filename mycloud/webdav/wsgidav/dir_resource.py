import asyncio
import inject
from wsgidav.dav_provider import DAVCollection
from mycloud.webdav.client import MyCloudDavClient, MyCloudMetadata
from mycloud.common import run_sync


class DirResource(DAVCollection):

    dav_client: MyCloudDavClient = inject.attr(MyCloudDavClient)

    def __init__(self, path, environ):
        super().__init__(path, environ)

    def get_member_names(self):
        metadata = self.dav_client.get_directory_metadata(self.path)
        def to_name(files): return list(map(lambda x: x.name, files))
        return to_name(metadata.dirs) + to_name(metadata.files)
