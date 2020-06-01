import inject
import asyncio
import os
from typing import Dict
from enum import Enum
from mycloud.mycloudapi.requests.drive import MyCloudMetadata, FileEntry, DirEntry, PutObjectRequest
from mycloud.drive import DriveClient
from mycloud.common import run_sync


class FileType(Enum):
    File = 0
    Dir = 1
    Enoent = 2


class Writable:

    def __init__(self, path, client, loop):
        self._path = path
        self._client: DriveClient = client
        self._loop = loop

    def writelines(self, stream):
        self._loop.run_until_complete(
            self._client.put_stream(self._path, stream))

    def close(self):
        pass


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

    def mkdirs(self, path):
        run_sync(self.drive_client.mkdirs(path))
        self.metadata_cache = dict()

    def open_read(self, path):
        loop = self._get_set_loop()
        return loop.run_until_complete(self.drive_client.open_read(path))

    def open_write(self, path):
        loop = self._get_set_loop()
        return Writable(path, self.drive_client, loop)

    def mkfile(self, path):
        run_sync(self.drive_client.mkfile(path))
        self.metadata_cache = dict()

    def remove(self, path, is_dir):
        run_sync(self.drive_client.delete(path, is_dir))
        self.metadata_cache = dict()

    def _get_metadata(self, path: str):
        if path in self.metadata_cache:
            return self.metadata_cache[path]
        metadata = run_sync(self.drive_client.get_directory_metadata(path))
        self.metadata_cache[path] = metadata
        return metadata

    def _get_set_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
