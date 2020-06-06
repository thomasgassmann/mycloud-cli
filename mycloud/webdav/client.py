import inject
import asyncio
import os
import threading
from typing import Dict
from enum import Enum
from wsgidav.util import get_uri_parent
from mycloud.mycloudapi.requests.drive import MyCloudMetadata, FileEntry, DirEntry, PutObjectRequest
from mycloud.drive import DriveClient, DriveNotFoundException


class FileType(Enum):
    File = 0
    Dir = 1
    Enoent = 2


class WriterWithCallback:
    def __init__(self, initial, callback):
        self._initial = initial
        self._callback = callback

    def write(self, bytes):
        self._initial.write(bytes)

    def close(self):
        self._initial.close()
        self._callback()


def thread_runner(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


class MyCloudDavClient:

    # make tree, update on other actions
    metadata_cache: Dict[str, MyCloudMetadata] = dict()
    # loops used to translate from sync to async paths
    # one per thread is needed
    drive_client: DriveClient = inject.attr(DriveClient)

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=thread_runner, args=(self._loop,))
        self._thread.start()

    def _run_sync(self, task):
        future = asyncio.run_coroutine_threadsafe(task, self._loop)
        return future.result()

    def get_file_type(self, path: str):
        normed = os.path.normpath(path)
        if normed == '/':
            return FileType.Dir

        basename = os.path.basename(normed)
        try:
            metadata = self._get_metadata(get_uri_parent(normed))
            def contains(l): return any(
                filter(lambda x: x.name == basename, l))
            if contains(metadata.files):
                return FileType.File
            if contains(metadata.dirs):
                return FileType.Dir
            return FileType.Enoent
        except DriveNotFoundException:
            return FileType.Enoent

    def get_directory_metadata(self, path):
        return self._get_metadata(path)

    def mkdirs(self, path):
        self._run_sync(self.drive_client.mkdirs(path))
        self._clear_cache(path)

    def open_read(self, path):
        return self._run_sync(self.drive_client.open_read(path))

    def open_write(self, path):
        temp = self._run_sync(self.drive_client.open_write(path))
        return WriterWithCallback(temp, lambda: self._clear_cache(path))

    def mkfile(self, path):
        self._run_sync(self.drive_client.mkfile(path))
        self._clear_cache(path)

    def remove(self, path, is_dir):
        self._run_sync(self.drive_client.delete(path, is_dir))
        self._clear_cache(path)

    def _clear_cache(self, path: str):
        dirname = get_uri_parent(path)
        normed = os.path.normpath(dirname)
        del self.metadata_cache[normed]

    def _get_metadata(self, path: str):
        path = os.path.normpath(path)
        if path in self.metadata_cache:
            return self.metadata_cache[path]
        metadata = self._run_sync(
            self.drive_client.get_directory_metadata(path))
        self.metadata_cache[path] = metadata
        return metadata
