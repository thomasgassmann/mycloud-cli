import click
from typing import List
from mycloud.filesync import upsync_folder
from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder


@click.command(name='upload')
@click.pass_context
@click.argument('local')
@click.argument('remote')
@click.option('--password', required=False)
@click.option('--skip', multiple=True, required=False, default=None)
@click.option('--skip_by_hash', is_flag=True, required=False, default=False)
def upload_command(ctx, local: str, remote: str, password: str, skip: List[str], skip_by_hash: bool):
    if skip is None:
        skip = []

    request_executor = ctx.obj['injector'].provide(MyCloudRequestExecutor)
    builder = ObjectResourceBuilder(local, remote)
    upsync_folder(
        request_executor,
        builder,
        local,
        _get_progress_tracker(skip),
        password,
        not skip_by_hash)


def _get_progress_tracker(skip_paths):
    tracker = ProgressTracker()
    if skip_paths is not None:
        skipped = ', '.join(skip_paths)
        tracker.set_skipped_paths(skip_paths)
    return tracker
