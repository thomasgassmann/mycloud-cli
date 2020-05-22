import click
import inject

from mycloud.commands.shared import (async_click, authenticated)
from mycloud.webdav import WebdavServer


@click.command(name='webdav')
@click.option('--host', nargs=1, required=True)
@click.option('--port', nargs=1, required=True)
@authenticated
@inject.params(server=WebdavServer)
@async_click
async def webdav_command(server: WebdavServer, host: str, port: int):
    await server.run(host, port)
