from typing import List

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.filesync import upsync_folder
from mycloud.drive import DriveNotFoundException, FsDriveClient


@click.command(name='downsync')
@click.argument('remote')
@click.argument('local')
@authenticated
@inject.params(client=FsDriveClient)
@async_click
async def downsync_command(client: FsDriveClient, remote: str, local: str):
    pass
