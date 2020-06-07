import asyncio
import logging
import os
from pathlib import Path

import inject

from mycloud.drive.drive_client import DriveClient, EntryType
from mycloud.drive.common import ls_files_recursively
from mycloud.drive.exceptions import DriveNotFoundException
from mycloud.mycloudapi import ObjectResourceBuilder


CHUNK_SIZE = 4096


class FsDriveClient:

    client: DriveClient = inject.attr(DriveClient)

    async def download(self, remote: str, local: str):
        remote_type = await self.client.stat(remote)
        if remote_type.entry_type == EntryType.Dir:
            await self.download_directory(remote, local)
        elif remote_type.entry_type == EntryType.File:
            await self.download_file(remote, local)
        else:
            raise DriveNotFoundException

    async def download_file(self, remote: str, local: str):
        stream = await self.client.open_read(remote)

        dir_name = os.path.dirname(local)
        if not os.path.isdir(dir_name):
            os.makedirs(os.path.dirname(local))
        local_stream = open(local, 'wb')
        while True:
            read = await stream.read_async(CHUNK_SIZE)
            if not read:
                break
            local_stream.write(read)
        stream.close()
        local_stream.close()

    async def download_directory(self, remote: str, local: str):
        builder = ObjectResourceBuilder(local, remote)

        async for file in ls_files_recursively(self.client, remote):
            local_path = builder.build_local_file(file.path)
            await self.download(file.path, local_path)

    async def upload(self, local: str, remote: str):
        if os.path.isdir(local):
            await self.upload_directory(local, remote)
        elif os.path.isfile(local):
            await self.upload_file(local, remote)
        else:
            raise FileNotFoundError

    async def upload_file(self, local: str, remote: str):
        if not os.path.isfile(local):
            raise FileNotFoundError

        stream = await self.client.open_write(remote)
        local_stream = open(local, 'rb')
        while True:
            chunk = local_stream.read(CHUNK_SIZE)
            if not chunk:
                break
            await stream.write_async(chunk)
        local_stream.close()
        stream.close()

    async def upload_directory(self, local: str, remote: str):
        if not os.path.isdir(local):
            raise FileNotFoundError

        builder = ObjectResourceBuilder(local, remote)
        for file in filter(lambda x: x.is_file(), Path(local).glob('**/*')):
            local_path = file.relative_to(local).as_posix()
            upload_path = builder.build_remote_file(local_path)
            await self.upload_file(local_path, upload_path)
