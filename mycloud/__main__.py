import click
from mycloud.commands import (
    auth_command,
    statistics_command,
    upload_command,
    download_command,
    convert_command
)
from mycloud.pinject import build_container


@click.group()
@click.pass_context
@click.option('--token', nargs=1, required=False)
def mycloud_cli(ctx, token):
    ctx.obj['injector'] = build_container(token=token)

mycloud_cli.add_command(auth_command)
mycloud_cli.add_command(statistics_command)
mycloud_cli.add_command(upload_command)
mycloud_cli.add_command(download_command)
mycloud_cli.add_command(convert_command)

if __name__ == '__main__':
    mycloud_cli(obj={})
