import logging
import os
import inject
from enum import Enum

from mycloud.common import to_generator
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


class DriveClient:

    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def list_files(self, remote: str):
        return await self._list_files_internal(remote)

    async def get_directory_metadata(self, path: str):
        return await self._get_directory_metadata_internal(path)

    async def download_each(self, directory_path: str, stream_factory):
        async for file in self._list_files_internal(directory_path):
            await self._download_internal(file['Path'], lambda: stream_factory(file))

    async def download(self, path: str, stream_factory):
        return await self._download_internal(path, stream_factory)

    async def upload(self, path: str, stream):
        generator = to_generator(stream)
        put_request = PutObjectRequest(path, generator)
        await self.request_executor.execute(put_request)

    async def delete(self, path: str):
        return await self._delete_internal(path)

    async def _download_internal(self, path, stream_factory):
        get_request = GetObjectRequest(path)
        resp: MyCloudResponse = await self.request_executor.execute(get_request)
        DriveClient._raise_404(resp)

        stream = stream_factory()
        while True:
            logging.debug(f'Reading download content...')
            chunk = await resp.result.content.read(CHUNK_SIZE)
            logging.debug(f'Got {len(chunk)} bytes')
            if not chunk:
                break
            logging.debug(f'Writing to output stream...')
            stream.write(chunk)
        stream.close()

    async def _delete_internal(self, path: str):
        try:
            await self._delete_single_internal(path)
        except DriveFailedToDeleteException:
            if not path.endswith('/'):
                raise  # probably an unrecoverable error, if it's not a directory

            metadata = await self._get_directory_metadata_internal(path)
            for remote_file in metadata.files:
                await self._delete_internal(remote_file.path)
            for directory in metadata.dirs:
                await self._delete_internal(directory.path)

    async def _delete_single_internal(self, path: str):
        delete_request = DeleteObjectRequest(path)
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
