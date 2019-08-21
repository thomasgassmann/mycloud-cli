import click
from mycloud.statistics import summarize, track_changes, print_usage, calculate_size
from mycloud.commands.shared import executor_from_ctx, async_click, authenticated


@click.group(name='statistics')
def statistics_command():
    pass


@statistics_command.command()
@click.pass_context
@click.argument('dir', required=True)
@authenticated
def summary(ctx, dir: str):
    request_executor = executor_from_ctx(ctx)
    summarize(request_executor, dir)


@statistics_command.command()
@click.pass_context
@click.argument('dir', required=True)
@click.argument('top', required=False, default=10)
@async_click
@authenticated
async def changes(ctx, dir: str, top: int):
    request_executor = executor_from_ctx(ctx)
    await track_changes(request_executor, dir, top)


@statistics_command.command()
@click.pass_context
@async_click
@authenticated
async def usage(ctx):
    request_executor = executor_from_ctx(ctx)
    await print_usage(request_executor)


@statistics_command.command()
@click.pass_context
@click.argument('dir', required=True)
@async_click
@authenticated
async def size(ctx, dir: str):
    request_executor = executor_from_ctx(ctx)
    await calculate_size(request_executor, dir)
