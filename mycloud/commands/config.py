from mycloud.constants import WEBDAV_CONFIG_LOCATION

from subprocess import call
import click
import os


def open_editor(file):
    EDITOR = os.environ.get('EDITOR', 'vim')
    call([EDITOR, file])


@click.group(name='config')
def config_command():
    pass


@config_command.command()
def webdav():
    open_editor(WEBDAV_CONFIG_LOCATION)
