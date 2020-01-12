import click
import inject

from mycloud.commands.shared import (async_click, authenticated)
from mycloud.photos import FsPhotosClient


@click.command(name='add')
@click.argument('local')
@click.argument('remote')
@authenticated
@inject.params(client=FsPhotosClient)
@async_click
async def add_command(client: FsPhotosClient, local: str, remote: str):
    await client.add(local, remote)
