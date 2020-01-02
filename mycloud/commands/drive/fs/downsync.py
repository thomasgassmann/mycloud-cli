from typing import List

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.filesync import downsync_folder
from mycloud.filesystem import BasicRemotePath
from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder


@click.command(name='downsync')
@click.argument('remote')
@click.argument('local')
@authenticated
@inject.params(executor=MyCloudRequestExecutor)
@async_click
async def downsync_command(executor: MyCloudRequestExecutor, remote: str, local: str):
    await downsync_folder(executor, ObjectResourceBuilder(
        local, remote), BasicRemotePath(remote), ProgressTracker())
