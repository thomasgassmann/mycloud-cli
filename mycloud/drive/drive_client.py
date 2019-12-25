import inject
import logging

from mycloud.constants import CHUNK_SIZE
from mycloud.mycloudapi import (MyCloudRequestExecutor, MyCloudResponse,
                                ObjectResourceBuilder)
from mycloud.mycloudapi.requests.drive import (DeleteObjectRequest,
                                               GetObjectRequest,
                                               PutObjectRequest,
                                               MetadataRequest)


class DriveClient:

    drive_base = '/Drive/'
    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def get_directory_metadata(self, path: str):
        full_path = self._build_path(path)
        req = MetadataRequest(full_path)
        resp = await self.request_executor.execute(req)
        return await resp.formatted()

    async def download(self, path: str, stream):
        full_path = self._build_path(path)
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
        full_path = self._build_path(path)

        def _read():
            while True:
                chunk = stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

        put_request = PutObjectRequest(full_path, _read())
        await self.request_executor.execute(put_request)

    async def delete(self, path: str):
        full_path = self._build_path(path)

        delete_request = DeleteObjectRequest(full_path)
        await self.request_executor.execute(delete_request)

    def _build_path(self, path: str):
        return ObjectResourceBuilder.combine_cloud_path(self.drive_base, path)
