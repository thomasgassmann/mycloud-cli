from typing import List

import click
import inject

from mycloud.commands.shared import (async_click, authenticated)
from mycloud.filesystem import FsDriveClient


@click.command(name='download')
@click.argument('remote')
@click.argument('local')
@authenticated
@inject.params(client=FsDriveClient)
@async_click
async def download_command(client: FsDriveClient, remote: str, local: str):
    await client.download(remote, local)
