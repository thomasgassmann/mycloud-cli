from typing import List
import click
from mycloud.commands.shared import executor_from_ctx
from mycloud.filesync import convert_remote_files


@click.command(name='convert')
@click.argument('remote')
@click.argument('local')
@click.option('--skip', required=False, default=None)
@click.pass_context
def convert_command(ctx, remote: str, local: str, skip: List[str]):
    request_executor = executor_from_ctx(ctx)
    convert_remote_files(
        request_executor,
        remote,
        local,
        skip or [])
