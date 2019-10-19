from typing import List
import click
import inject
from mycloud.filesync import downsync_folder
from mycloud.mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from mycloud.filesystem import BasicRemotePath
from mycloud.commands.shared import (
    get_progress_tracker,
    async_click,
    authenticated
)


@click.command(name='download')
@click.argument('remote')
@click.argument('local')
@click.option('--password', required=False)
@click.option('--skip', multiple=True, required=False, default=None)
@click.option('--skip_by_hash', is_flag=True, required=False, default=False)
@authenticated
@inject.params(executor=MyCloudRequestExecutor)
@async_click
async def download_command(executor: MyCloudRequestExecutor, remote: str, local: str, password: str, skip: List[str], skip_by_hash: bool):
    if skip is None:
        skip = []

    builder = ObjectResourceBuilder(local, remote)
    tracker = get_progress_tracker(skip)
    await downsync_folder(
        executor,
        builder,
        BasicRemotePath(remote),
        tracker,
        password)
