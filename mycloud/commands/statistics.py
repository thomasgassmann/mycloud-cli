import click
from mycloud.statistics import summarize, track_changes, print_usage, calculate_size
from mycloud.mycloudapi import MyCloudRequestExecutor


@click.group(name='statistics')
def statistics_command():
    pass


@statistics_command.command()
@click.pass_context
@click.argument('dir', str, required=True)
def summary(ctx, dir: str):
    request_executor = ctx.obj['injector'].provide(MyCloudRequestExecutor)
    summarize(request_executor, dir)


@statistics_command.command()
@click.pass_context
@click.argument('dir', str, required=True)
@click.argument('top', int, required=False, default=10)
def changes(ctx, dir: str, top: int):
    request_executor = ctx.obj['injector'].provide(MyCloudRequestExecutor)
    track_changes(request_executor, dir, top)


@statistics_command.command()
@click.pass_context
def usage(ctx):
    request_executor = ctx.obj['injector'].provide(MyCloudRequestExecutor)
    print_usage(request_executor)


@statistics_command.command()
@click.pass_context
@click.argument('dir', str, required=True)
def size(ctx, dir: str):
    request_executor = ctx.obj['injector'].provide(MyCloudRequestExecutor)
    calculate_size(request_executor, dir)
