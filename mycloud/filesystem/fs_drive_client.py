import asyncio
import logging
import os
from pathlib import Path

import inject

from mycloud.drive import DriveClient
from mycloud.mycloudapi import ObjectResourceBuilder


class FsDriveClient:

    client: DriveClient = inject.attr(DriveClient)

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
                        with file.open('rb') as f:
                            await self.client.upload(upload_path, f)
                    # TODO: parallelize
                    await _up()
        else:
            raise ValueError(f'No valid file type {local}')
