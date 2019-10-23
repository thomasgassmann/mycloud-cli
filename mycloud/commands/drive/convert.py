from typing import List
import click
import inject
from mycloud.commands.shared import async_click, authenticated
from mycloud.filesync import convert_remote_files
from mycloud.mycloudapi import MyCloudRequestExecutor


@click.command(name='convert')
@click.argument('remote')
@click.argument('local')
@click.option('--skip', required=False, default=None)
@authenticated
@inject.params(request_executor=MyCloudRequestExecutor)
@async_click
async def convert_command(request_executor: MyCloudRequestExecutor, remote: str, local: str, skip: List[str]):
    await convert_remote_files(
        request_executor,
        remote,
        local,
        skip or [])
