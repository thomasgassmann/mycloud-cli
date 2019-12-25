import os
from typing import List
from pathlib import Path

import click
import inject

from mycloud.commands.shared import (async_click, authenticated)
from mycloud.filesystem import FsDriveClient


@click.command(name='upload')
@click.argument('local')
@click.argument('remote')
@authenticated
@inject.params(client=FsDriveClient)
@async_click
async def upload_command(client: FsDriveClient, local: str, remote: str):
    await client.upload(local, remote)
