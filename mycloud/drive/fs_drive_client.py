import asyncio
import logging
import os
from pathlib import Path

import inject

from mycloud.drive.drive_client import DriveClient, FileType
from mycloud.mycloudapi import ObjectResourceBuilder


class FsDriveClient:

    client: DriveClient = inject.attr(DriveClient)

    async def download(self, remote: str, local: str):
        file_type = await self.client.get_path_metadata(remote)
        if file_type == FileType.Directory:
            await self.download_directory(remote, local)
        else:
            await self.download_file(remote, local)

    async def download_file(self, remote: str, local: str):

        def stream_factory():
            dir_name = os.path.dirname(local)
            if not os.path.isdir(dir_name):
                os.makedirs(os.path.dirname(local))

            return open(local, 'wb')

        await self.client.download(remote, stream_factory)

    async def download_directory(self, remote: str, local: str):
        builder = ObjectResourceBuilder(local, remote)

        def stream_factory(file):
            remote_file_path = file['Path']
            file_path = builder.build_local_file(remote_file_path)
            logging.debug(
                f'Stream factory built download path {file_path} for item {remote_file_path}')
            dir_path = os.path.dirname(file_path)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            return open(file_path, 'wb')

        await self.client.download_each(remote, stream_factory)

    async def upload(self, local: str, remote: str):
        builder = ObjectResourceBuilder(local, remote)
        if os.path.isfile(local):
            logging.debug(f'{local} is file...')
            with open(local, 'rb') as f:
                await self.client.upload(remote, f)
        elif os.path.isdir(local):
            logging.debug(f'{local} is directory...')
            for file in Path(local).glob('**/*'):
                if file.is_file():
                    upload_path = builder.build_remote_file(
                        file.relative_to(local).as_posix())

                    async def _up():
                        logging.info(f'Uploading {file}...')
                        try:
                            f = file.open('rb')
                        except PermissionError:
                            logging.error(f'Could not access file {file}')
                            return
                        await self.client.upload(upload_path, f)
                        f.close()
                    # TODO: parallelize
                    await _up()
        else:
            raise ValueError(f'No valid file type {local}')
