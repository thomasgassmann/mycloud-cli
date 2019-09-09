import getpass
import click
import inject
from halo import Halo
from mycloud.mycloudapi.auth import MyCloudAuthenticator
from mycloud.mycloudapi.auth.bearer_token import open_for_cert
from mycloud.commands.shared import container, provide, async_click, authenticated
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
    await storage.save(user, password, skip_validation=False, no_headless_validation=no_headless)


@auth_command.command()
@async_click
async def cert():
    await open_for_cert()


@auth_command.command()
@click.pass_context
@async_click
@authenticated
async def token(ctx):
    injector = container(ctx)
    authenticator = provide(ctx, MyCloudAuthenticator)
    authenticator.invalidate_token()
    token_to_print = await authenticator.get_token()
    click.echo(token_to_print)
