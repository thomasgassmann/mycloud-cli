import getpass
import click
from halo import Halo
from mycloud.mycloudapi.auth import MyCloudAuthenticator
from mycloud.mycloudapi.auth.bearer_token import open_for_cert
from mycloud.commands.shared import container, provide, async_click, authenticated
from mycloud.credentials import CredentialStorage


@click.group(name='auth')
def auth_command():
    pass


@auth_command.command()
@click.pass_context
@async_click
# TODO: click.password_option()
async def login(ctx):
    credential_storage: CredentialStorage = provide(ctx, CredentialStorage)
    user = input('Email: ')
    password = getpass.getpass()
    await credential_storage.save(user, password)


@auth_command.command()
def cert():
    open_for_cert()


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
