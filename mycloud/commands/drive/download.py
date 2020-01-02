from typing import List

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.drive import DriveNotFoundException, FsDriveClient


@click.command(name='download')
@click.argument('remote')
@click.argument('local')
@authenticated
@inject.params(client=FsDriveClient)
@async_click
async def download_command(client: FsDriveClient, remote: str, local: str):
    try:
        await client.download(remote, local)
    except DriveNotFoundException:
        raise click.ClickException(f'{remote} not found')
