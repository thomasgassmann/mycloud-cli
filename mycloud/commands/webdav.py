import click
import inject

from mycloud.commands.shared import authenticated
from mycloud.webdav import WebdavServer


@click.command(name='webdav')
@click.option('--host', nargs=1, required=True)
@click.option('--port', nargs=1, required=True)
@authenticated
@inject.params(server=WebdavServer)
def webdav_command(server: WebdavServer, host: str, port: int):
    server.run(host, port)
