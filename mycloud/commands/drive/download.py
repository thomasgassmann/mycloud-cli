from typing import List

import click
import inject

from mycloud.commands.shared import (async_click, authenticated)
from mycloud.drive import DriveClient


@click.command(name='download')
@click.argument('remote')
@click.argument('local')
@authenticated
@inject.params(client=DriveClient)
@async_click
async def download_command(client: DriveClient, remote: str, local: str):
    with open(local, 'wb') as handle:
        await client.download(remote, handle)
