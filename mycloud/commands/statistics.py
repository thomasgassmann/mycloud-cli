import click
from mycloud.statistics.summarizer import summarize
from mycloud.mycloudapi import MyCloudRequestExecutor


@click.group(name='statistics')
def statistics_command():
    pass


@statistics_command.command()
@click.pass_context
@click.argument('dir', required=True)
def summary(ctx, dir: str):
    request_executor = ctx.obj['injector'].provide(MyCloudRequestExecutor)
    summarize(request_executor, dir)
