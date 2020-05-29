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
                                               PutObjectRequest)


DRIVE_BASE = '/Drive'


class FileType(Enum):
    DoesNotExist = 0
    Directory = 1
    File = 2


class DriveClient:

    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def list_files(self, remote: str):
        remote = DriveClient._sanitize_path(remote, force_dir=True)
        return await self._list_files_internal(remote)

    async def get_directory_metadata(self, path: str):
        path = DriveClient._sanitize_path(
            path, force_dir=True)
        return await self._get_directory_metadata_internal(path)

    async def get_path_metadata(self, remote: str) -> FileType:
        if remote == '/':
            return FileType.Directory

        remote = DriveClient._sanitize_path(remote, force_file=True)
        directory = os.path.dirname(remote)
        try:
            (dirs, files) = await self._get_directory_metadata_internal(directory)
            if remote in files:
                return FileType.File
            return FileType.Directory
        except:
            return FileType.DoesNotExist

    async def download_each(self, directory_path: str, stream_factory):
        directory_path = DriveClient._sanitize_path(
            directory_path, force_dir=True)
        async for file in self._list_files_internal(directory_path):
            await self._download_internal(file['Path'], lambda: stream_factory(file))

    async def download(self, path: str, stream_factory):
        path = DriveClient._sanitize_path(path, force_file=True)
        return await self._download_internal(path, stream_factory)

    async def upload(self, path: str, stream):
        path = DriveClient._sanitize_path(path, force_file=True)

        generator = to_generator(stream)
        put_request = PutObjectRequest(path, generator)
        await self.request_executor.execute(put_request)

    async def delete(self, path: str):
        path = DriveClient._sanitize_path(path)
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

            (dirs, files) = await self._get_directory_metadata_internal(path)
            for remote_file in files:
                await self._delete_internal(remote_file['Path'])
            for directory in dirs:
                await self._delete_internal(directory['Path'])

    async def _delete_single_internal(self, path: str):
        delete_request = DeleteObjectRequest(path)
        resp = await self.request_executor.execute(delete_request)
        DriveClient._raise_404(resp)
        if not resp.success:
            logging.info(f'Failed to delete {path}')
            raise DriveFailedToDeleteException

    async def _get_directory_metadata_internal(self, path: str):
        req = MetadataRequest(path)
        resp = await self.request_executor.execute(req)
        DriveClient._raise_404(resp)

        return await resp.formatted()

    async def _list_files_internal(self, path: str):
        (directories, fetched_files) = await self._get_directory_metadata_internal(path)
        for file in fetched_files:
            yield file

        for sub_directory in directories:
            async for file in self._list_files_internal(sub_directory['Path']):
                yield file

    @staticmethod
    def _raise_404(response: MyCloudResponse):
        if response.result.status == 404:
            raise DriveNotFoundException

    @staticmethod
    def _sanitize_path(path: str, force_dir=False, force_file=False) -> str:
        res = DRIVE_BASE + path
        if force_dir:
            return res + '/' if not res.endswith('/') else res

        if force_file:
            return res[:-1] if res.endswith('/') else res

        return res
