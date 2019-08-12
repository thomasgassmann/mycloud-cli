from typing import List
import click
from mycloud.filesync import upsync_folder
from mycloud.mycloudapi import ObjectResourceBuilder
from mycloud.commands.shared import get_progress_tracker, executor_from_ctx


@click.command(name='upload')
@click.pass_context
@click.argument('local')
@click.argument('remote')
@click.option('--password', required=False)
@click.option('--skip', multiple=True, required=False, default=None)
@click.option('--skip_by_hash', is_flag=True, required=False, default=False)
async def upload_command(ctx, local: str, remote: str, password: str, skip: List[str], skip_by_hash: bool):
    if skip is None:
        skip = []

    request_executor = executor_from_ctx(ctx)
    builder = ObjectResourceBuilder(local, remote)
    await upsync_folder(
        request_executor,
        builder,
        local,
        get_progress_tracker(skip),
        password,
        not skip_by_hash)
