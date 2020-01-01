import logging

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.drive import DriveClient, DriveFailedToDeleteException
from mycloud.mycloudapi.requests.drive import (DeleteObjectRequest,
                                               MetadataRequest)


@click.command(name='delete')
@click.argument('remote')
@authenticated
@inject.params(client=DriveClient)
@async_click
async def delete_command(remote: str, client: DriveClient):
    try:
        await client.delete(remote)
    except DriveFailedToDeleteException:
        raise click.ClickException(f'Failed to delete {remote}')
