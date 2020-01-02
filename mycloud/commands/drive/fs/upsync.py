from typing import List

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.filesync import upsync_folder
from mycloud.drive import DriveNotFoundException, FsDriveClient


@click.command(name='upsync')
@click.argument('remote')
@click.argument('local')
@authenticated
@inject.params(client=FsDriveClient)
@async_click
async def upsync_command(client: FsDriveClient, remote: str, local: str):
    pass
