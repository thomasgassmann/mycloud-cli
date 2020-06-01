import inject
import os
from typing import Dict
from enum import Enum
from mycloud.mycloudapi.requests.drive import MyCloudMetadata, FileEntry, DirEntry
from mycloud.drive import DriveClient
from mycloud.common import run_sync


class FileType(Enum):
    File = 0
    Dir = 1
    Enoent = 2


class MyCloudDavClient:

    metadata_cache: Dict[str, MyCloudMetadata] = dict()
    drive_client: DriveClient = inject.attr(DriveClient)

    def get_file_type(self, path: str):
        normed = os.path.normpath(path)
        if normed == '/':
            return FileType.Dir

        basename = os.path.basename(normed)
        try:
            metadata = self._get_metadata(os.path.dirname(normed))
            def contains(l): return any(
                filter(lambda x: x.name == basename, l))
            if contains(metadata.files):
                return FileType.File
            if contains(metadata.dirs):
                return FileType.Dir
            return FileType.Enoent
        except:
            return FileType.Enoent

    def get_directory_metadata(self, path):
        normed = os.path.normpath(path)
        return self._get_metadata(normed)

    def remove(self, path):
        normed = os.path.normpath(path)
        run_sync(self.drive_client.delete(normed))
        self.metadata_cache = dict()

    def _get_metadata(self, path: str):
        if path in self.metadata_cache:
            return self.metadata_cache[path]
        metadata = run_sync(self.drive_client.get_directory_metadata(path))
        self.metadata_cache[path] = metadata
        return metadata
