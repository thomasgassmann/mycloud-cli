from typing import List

import click
import inject

from mycloud.commands.shared import (async_click, authenticated)
from mycloud.drive import DriveClient


@click.command(name='upload')
@click.argument('local')
@click.argument('remote')
@authenticated
@inject.params(client=DriveClient)
@async_click
async def upload_command(client: DriveClient, local: str, remote: str):
    with open(local, 'rb') as handle:
        await client.upload(remote, handle)
