import logging

import inject

from mycloud.constants import CHUNK_SIZE
from mycloud.drive.exceptions import DriveNotFoundException
from mycloud.mycloudapi import (MyCloudRequestExecutor, MyCloudResponse,
                                ObjectResourceBuilder)
from mycloud.mycloudapi.requests.drive import (DeleteObjectRequest,
                                               GetObjectRequest,
                                               MetadataRequest,
                                               PutObjectRequest)


class DriveClient:

    drive_base = '/Drive/'
    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def list_files(self, remote: str):
        (directories, fetched_files) = await self.get_directory_metadata(remote)
        for file in fetched_files:
            yield file

        for sub_directory in directories:
            async for file in self.list_files(sub_directory['Path']):
                yield file

    async def get_directory_metadata(self, path: str):
        full_path = self.build_path(path)
        req = MetadataRequest(full_path)
        resp = await self.request_executor.execute(req)
        if resp.result.status == 404:
            raise DriveNotFoundException()

        return await resp.formatted()

    async def download_each(self, directory_path: str, stream_factory):
        async for file in self.list_files(directory_path):
            with stream_factory(file) as stream:
                await self.download(file['Path'], stream)

    async def download(self, path: str, stream):
        full_path = self.build_path(path)
        get_request = GetObjectRequest(full_path)
        resp: MyCloudResponse = await self.request_executor.execute(get_request)
        while True:
            logging.debug(f'Reading download content...')
            chunk = await resp.result.content.read(CHUNK_SIZE)
            logging.debug(f'Got {len(chunk)} bytes')
            if not chunk:
                break
            logging.debug(f'Writing to output stream...')
            stream.write(chunk)

    async def upload(self, path: str, stream):
        full_path = self.build_path(path)

        def _read():
            while True:
                chunk = stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

        put_request = PutObjectRequest(full_path, _read())
        await self.request_executor.execute(put_request)

    async def delete(self, path: str):
        full_path = self.build_path(path)

        delete_request = DeleteObjectRequest(full_path)
        await self.request_executor.execute(delete_request)

    def build_path(self, path: str):
        built_path = path if path.startswith(self.drive_base) else ObjectResourceBuilder.combine_cloud_path(
            self.drive_base, path)
        logging.info(f'Constructed path {built_path}')
        return built_path
