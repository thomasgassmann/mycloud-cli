from typing import List
import click
from mycloud.filesync import downsync_folder
from mycloud.mycloudapi import ObjectResourceBuilder
from mycloud.filesystem import BasicRemotePath
from mycloud.commands.shared import get_progress_tracker, executor_from_ctx, async_click


@click.command(name='download')
@click.pass_context
@click.argument('remote')
@click.argument('local')
@click.option('--password', required=False)
@click.option('--skip', multiple=True, required=False, default=None)
@click.option('--skip_by_hash', is_flag=True, required=False, default=False)
@async_click
async def download_command(ctx, remote: str, local: str, password: str, skip: List[str], skip_by_hash: bool):
    if skip is None:
        skip = []

    executor = executor_from_ctx(ctx)
    builder = ObjectResourceBuilder(local, remote)
    tracker = get_progress_tracker(skip)
    await downsync_folder(
        executor,
        builder,
        BasicRemotePath(remote),
        tracker,
        password)
