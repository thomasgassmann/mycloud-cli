import os

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.drive.filesync import upsync_folder
from mycloud.drive.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder


@click.command(name='upsync')
@click.argument('local')
@click.argument('remote')
@authenticated
@inject.params(executor=MyCloudRequestExecutor)
@async_click
async def upsync_command(executor: MyCloudRequestExecutor, local: str, remote: str):
    resource_builder = ObjectResourceBuilder(local, remote)
    local = os.path.abspath(local)
    await upsync_folder(executor, resource_builder, local, ProgressTracker())
