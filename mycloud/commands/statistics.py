import click
from mycloud.statistics.summarizer import summarize


@click.group(name='statistics')
def statistics_command():
    pass


@statistics_command.command()
@click.pass_context
def summary(ctx):
    print(ctx.obj['token'])
