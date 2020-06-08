import logging
import asyncio
import os
import inject
from enum import Enum
from typing import List, AsyncIterator
from datetime import datetime
from collections import deque
from threading import Thread
from dataclasses import dataclass
from mycloud.constants import CHUNK_SIZE
from mycloud.drive.exceptions import (DriveFailedToDeleteException,
                                      DriveNotFoundException)
from mycloud.mycloudapi import (MyCloudRequestExecutor, MyCloudResponse,
                                ObjectResourceBuilder)
from mycloud.mycloudapi.requests.drive import (DeleteObjectRequest,
                                               GetObjectRequest,
                                               MetadataRequest,
                                               PutObjectRequest,
                                               MyCloudMetadata,
                                               RenameRequest,
                                               FileEntry,
                                               DirEntry)


class ReadStream:

    def __init__(self, content):
        self._content = content
        self._loop = asyncio.get_event_loop()

    def read(self, length):
        res = asyncio.run_coroutine_threadsafe(
            self._content.read(length), self._loop)
        return res.result()

    async def read_async(self, length):
        return await self._content.read(length)

    def close(self):
        pass


class WriteStream:

    def __init__(self, exec_stream):
        self._loop = asyncio.get_event_loop()
        self._exec = exec_stream
        # TODO: queue size should depend on size of individual items?
        self._queue = asyncio.Queue(maxsize=1)
        self._closed = False
        self._thread = None
        self._start()

    def write(self, bytes):
        self._put_queue(bytes)

    def writelines(self, stream):
        for item in stream:
            self._put_queue(item)

    async def write_async(self, bytes):
        await self._put_queue_async(bytes)

    def close(self):
        self._closed = True
        if self._thread:
            self._thread.join()
        del self._queue

    async def _put_queue_async(self, item):
        await self._queue.put(item)

    def _put_queue(self, item):
        asyncio.run_coroutine_threadsafe(
            self._queue.put(item), self._loop).result()

    def _start(self):
        def r():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._exec(self._generator(loop)))
        self._thread = Thread(target=r)
        self._thread.start()

    def _generator(self, loop):
        while not self._closed or not self._queue.empty():
            if not self._queue.empty():  # TODO: should be done with asyncio
                yield self._queue.get_nowait()


class EntryType(Enum):
    File = 0
    Dir = 1
    Enoent = 2


@dataclass
class EntryStats:
    entry_type: EntryType
    name: str
    path: str
    creation_time: datetime
    modification_time: datetime


NO_ENTRY = EntryStats(EntryType.Enoent, '', '', datetime.min, datetime.min)
ROOT_ENTRY = EntryStats(EntryType.Dir, '/', '/', datetime.min, datetime.min)


class DriveClient:

    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def ls(self, remote: str) -> MyCloudMetadata:
        return await self._get_directory_metadata_internal(remote)

    async def stat(self, path: str):
        normed = os.path.normpath(path)
        if normed == '/':
            return ROOT_ENTRY

        basename = os.path.basename(normed)
        try:
            metadata = await self.ls(os.path.dirname(normed))

            def first(l):
                try:
                    return next(filter(lambda x: x.name == basename, l))
                except StopIteration:
                    return None
            file = first(metadata.files)
            if file is not None:
                return EntryStats(
                    EntryType.File,
                    name=file.name,
                    path=file.path,
                    creation_time=file.creation_time,
                    modification_time=file.modification_time)
            directory = first(metadata.dirs)
            if directory is not None:
                return EntryStats(
                    EntryType.Dir,
                    name=directory.name,
                    path=directory.path,
                    creation_time=directory.creation_time,
                    modification_time=directory.modification_time)
            return NO_ENTRY
        except DriveNotFoundException:
            return NO_ENTRY

    async def open_read(self, path: str):
        get = GetObjectRequest(path, is_dir=False)
        resp = await self.request_executor.execute(get)
        DriveClient._raise_404(resp)
        return ReadStream(resp.result.content)

    async def open_write(self, path: str):
        def exec_stream(g):
            return self.request_executor.execute(
                PutObjectRequest(path, g, is_dir=False))

        return WriteStream(exec_stream)

    async def mkfile(self, path: str):
        put_request = PutObjectRequest(path, None, False)
        await self.request_executor.execute(put_request)

    async def mkdirs(self, path: str):
        put_request = PutObjectRequest(path, None, True)
        await self.request_executor.execute(put_request)

    async def move(self, from_path, to_path):
        stat = await self.stat(from_path)
        rename_request = RenameRequest(
            from_path, to_path, stat.is_file)
        await self.request_executor.execute(rename_request)

    async def copy(self, from_path, to_path):
        pass

    async def delete(self, path: str):
        stat = await self.stat(path)
        return await self._delete_internal(path, stat.entry_type == EntryType.Dir)

    async def _delete_internal(self, path: str, is_dir):
        try:
            await self._delete_single_internal(path, is_dir)
        except DriveFailedToDeleteException:
            if not is_dir:
                raise  # probably an unrecoverable error, if it's not a directory

            metadata = await self._get_directory_metadata_internal(path)
            for remote_file in metadata.files:
                await self._delete_internal(remote_file.path, False)
            for directory in metadata.dirs:
                await self._delete_internal(directory.path, True)

    async def _delete_single_internal(self, path: str, is_dir):
        delete_request = DeleteObjectRequest(path, is_dir)
        resp = await self.request_executor.execute(delete_request)
        DriveClient._raise_404(resp)
        if not resp.success:
            logging.info(f'Failed to delete {path}')
            raise DriveFailedToDeleteException

    async def _get_directory_metadata_internal(self, path: str) -> MyCloudMetadata:
        req = MetadataRequest(path)
        resp = await self.request_executor.execute(req)
        DriveClient._raise_404(resp)

        return await resp.formatted()

    @staticmethod
    def _raise_404(response: MyCloudResponse):
        if response.result.status == 404:
            raise DriveNotFoundException
