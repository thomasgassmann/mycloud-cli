from typing import List
import click
import inject
from mycloud.filesync import upsync_folder
from mycloud.mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from mycloud.commands.shared import (
    get_progress_tracker,
    async_click,
    authenticated
)


@click.command(name='upload')
@click.argument('local')
@click.argument('remote')
@click.option('--password', required=False)
@click.option('--skip', multiple=True, required=False, default=None)
@click.option('--skip_by_hash', is_flag=True, required=False, default=False)
@authenticated
@inject.params(executor=MyCloudRequestExecutor)
@async_click
async def upload_command(executor: MyCloudRequestExecutor, local: str, remote: str, password: str, skip: List[str], skip_by_hash: bool):
    if skip is None:
        skip = []

    builder = ObjectResourceBuilder(local, remote)
    await upsync_folder(
        executor,
        builder,
        local,
        get_progress_tracker(skip),
        password,
        not skip_by_hash)
