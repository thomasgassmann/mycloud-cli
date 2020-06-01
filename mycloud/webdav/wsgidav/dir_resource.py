import asyncio
import inject
import os
from wsgidav.dav_provider import DAVCollection
from mycloud.webdav.client import MyCloudDavClient, MyCloudMetadata
from mycloud.common import run_sync, to_unix


class DirResource(DAVCollection):

    dav_client: MyCloudDavClient = inject.attr(MyCloudDavClient)

    def __init__(self, path, environ):
        super().__init__(path, environ)

    def get_creation_date(self):
        return to_unix(self._metadata.creation_time)

    def get_last_modified(self):
        return to_unix(self._metadata.modification_time)

    def get_display_name(self):
        return self._metadata.name

    def get_member_names(self):
        def to_name(files): return list(map(lambda x: x.name, files))
        return to_name(self._metadata.dirs) + to_name(self._metadata.files)

    def create_collection(self, name):
        new_path = os.path.join(self.path, name)
        self.dav_client.mkdirs(new_path)

    def delete(self):
        self.dav_client.remove(self.path, is_dir=True)
        self.remove_all_properties(True)
        self.remove_all_locks(True)

    @property
    def _metadata(self):
        return self.dav_client.get_directory_metadata(self.path)