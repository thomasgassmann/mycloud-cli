import click
import inject
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.statistics import summarize, track_changes, print_usage, calculate_size
from mycloud.commands.shared import async_click, authenticated


@click.group(name='statistics')
def statistics_command():
    pass


@statistics_command.command()
@inject.params(executor=MyCloudRequestExecutor)
@click.argument('dir', required=True)
@authenticated
def summary(executor, dir: str):
    summarize(executor, dir)


@statistics_command.command()
@inject.params(executor=MyCloudRequestExecutor)
@click.argument('dir', required=True)
@click.argument('top', required=False, default=10)
@authenticated
@async_click
async def changes(executor, dir: str, top: int):
    await track_changes(executor, dir, top)


@statistics_command.command()
@inject.params(executor=MyCloudRequestExecutor)
@authenticated
@async_click
async def usage(executor):
    await print_usage(executor)


@statistics_command.command()
@click.argument('dir', required=True)
@inject.params(executor=MyCloudRequestExecutor)
@authenticated
@async_click
async def size(dir: str, executor):
    await calculate_size(executor, dir)
