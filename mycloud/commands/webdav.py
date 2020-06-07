import click
import inject

from mycloud.commands.shared import authenticated
from mycloud.webdav import WebdavServer


@click.command(name='webdav')
@click.option('--host', nargs=1, required=True)
@click.option('--port', nargs=1, required=True)
@click.option('--skip-credential-validation', required=False, is_flag=True, default=False)
@click.option('--folder-creation-in-cache', required=False, is_flag=True, default=False)
@authenticated
@inject.params(server=WebdavServer)
def webdav_command(server: WebdavServer, host: str, port: int, skip_credential_validation: bool, folder_creation_in_cache: bool):
    server.run(host, port, not skip_credential_validation)
