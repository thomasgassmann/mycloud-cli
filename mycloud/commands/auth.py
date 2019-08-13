import getpass
import click
from halo import Halo
from mycloud.mycloudapi.auth.bearer_token import open_for_cert
from mycloud.commands.shared import container, provide
from mycloud.credentials import CredentialStorage


@click.group(name='auth')
def auth_command():
    pass


@auth_command.command()
@Halo(text='Saving credentials...', spinner='dots')
@click.pass_context
# TODO: click.password_option()
def login(ctx):
    credential_storage: CredentialStorage = provide(ctx, CredentialStorage)
    user = input('Email: ')
    password = getpass.getpass()
    credential_storage.save(user, password)


@auth_command.command()
def cert():
    open_for_cert()


@auth_command.command()
@click.pass_context
async def token(ctx):
    class _Proxy:
        def __init__(self, mycloud_authenticator):
            self.val = mycloud_authenticator

    injector = container(ctx)
    authenticator = injector.provide(_Proxy).val
    authenticator.invalidate_token()
    token_to_print = await authenticator.get_token()
    click.echo(token_to_print)
