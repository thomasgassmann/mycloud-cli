import sys
import logging
import click
from mycloud.commands import (
    auth_command,
    statistics_command
)
from mycloud.commands.drive import (
    upload_command,
    download_command,
    convert_command,
    delete_command
)
from mycloud.pinject import build_container


def get_log_level(level_str: str) -> int:
    try:
        return getattr(logging, level_str) if level_str else logging.INFO
    except AttributeError:
        raise click.ClickException(f'Log level {level_str} not found.')


def setup_logger(level_str: str, log_file: str):
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(get_log_level(level_str))

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


@click.group()
@click.pass_context
@click.option('--token', nargs=1, required=False)
@click.option('--log-level', nargs=1, required=False)
@click.option('--log-file', nargs=1, required=False)
def mycloud_cli(ctx: click.Context, token: str, log_level: str, log_file: str):
    setup_logger(log_level, log_file)
    ctx.obj['injector'] = build_container(token=token)


@click.group(name='drive')
def drive_cli():
    pass


drive_cli.add_command(delete_command)
drive_cli.add_command(upload_command)
drive_cli.add_command(download_command)
drive_cli.add_command(convert_command)

mycloud_cli.add_command(drive_cli)
mycloud_cli.add_command(auth_command)
mycloud_cli.add_command(statistics_command)

if __name__ == '__main__':
    sys.argv = list(filter(lambda x: x is not None and str(x).strip() != '', sys.argv))

    mycloud_cli(obj={})
