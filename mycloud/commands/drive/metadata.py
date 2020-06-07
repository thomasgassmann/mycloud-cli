import logging

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.drive import DriveClient


@click.command(name='metadata')
@click.argument('remote')
@authenticated
@inject.params(client=DriveClient)
@async_click
async def metadata_command(remote: str, client: DriveClient):
    metadata = await client.ls(remote)
    click.echo(metadata)
