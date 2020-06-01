import logging
import asyncio
import os
import inject
from enum import Enum

from mycloud.common import to_generator, run_sync
from mycloud.constants import CHUNK_SIZE
from mycloud.drive.exceptions import (DriveFailedToDeleteException,
                                      DriveNotFoundException)
from mycloud.mycloudapi import (MyCloudRequestExecutor, MyCloudResponse,
                                ObjectResourceBuilder)
from mycloud.mycloudapi.requests.drive import (DeleteObjectRequest,
                                               GetObjectRequest,
                                               MetadataRequest,
                                               PutObjectRequest,
                                               MyCloudMetadata)


class ReadStream:

    def __init__(self, content, loop):
        self._content = content
        self._loop = loop

    def read(self, length):
        return self._loop.run_until_complete(self._content.read(length))

    def close(self):
        pass


class DriveClient:

    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def list_files(self, remote: str):
        return await self._list_files_internal(remote)

    async def get_directory_metadata(self, path: str):
        return await self._get_directory_metadata_internal(path)

    async def open_read(self, path: str):
        get = GetObjectRequest(path, is_dir=False)
        resp = await self.request_executor.execute(get)
        DriveClient._raise_404(resp)
        return ReadStream(resp.result.content, asyncio.get_event_loop())

    async def put_stream(self, path: str, generator):
        req = PutObjectRequest(path, generator, is_dir=False)
        resp = await self.request_executor.execute(req)

    async def mkfile(self, path: str):
        put_request = PutObjectRequest(path, None, False)
        await self.request_executor.execute(put_request)

    async def mkdirs(self, path: str):
        put_request = PutObjectRequest(path, None, True)
        await self.request_executor.execute(put_request)

    async def delete(self, path: str, is_dir):
        return await self._delete_internal(path, is_dir)

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

    async def _list_files_internal(self, path: str):
        metadata = await self._get_directory_metadata_internal(path)
        for file in metadata.files:
            yield file

        for sub_directory in metadata.dirs:
            async for file in self._list_files_internal(sub_directory.path):
                yield file

    @staticmethod
    def _raise_404(response: MyCloudResponse):
        if response.result.status == 404:
            raise DriveNotFoundException
