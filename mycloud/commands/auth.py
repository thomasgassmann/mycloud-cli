import getpass
import click
import inject
from halo import Halo
from mycloud.mycloudapi.auth import MyCloudAuthenticator
from mycloud.mycloudapi.auth.bearer_token import open_for_cert
from mycloud.commands.shared import async_click, authenticated
from mycloud.credentials import CredentialStorage


@click.group(name='auth')
def auth_command():
    pass


@auth_command.command()
@click.option('--no-headless', required=False, is_flag=True, default=False)
@inject.params(storage=CredentialStorage)
@async_click
# TODO: click.password_option()
async def login(storage: CredentialStorage, no_headless):
    user = input('Email: ')
    password = getpass.getpass()
    res = await storage.save(user, password, skip_validation=False, no_headless_validation=no_headless)
    if res:
        click.echo('Successfully authenticated!')
    else:
        click.echo('Failed to authenticate')


@auth_command.command()
@async_click
async def cert():
    await open_for_cert()


@auth_command.command()
@inject.params(auth=MyCloudAuthenticator)
@authenticated
@async_click
async def token(auth):
    auth.invalidate_token()
    token_to_print = await auth.get_token()
    click.echo(token_to_print)
