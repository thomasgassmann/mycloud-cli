import getpass
import click
from halo import Halo
from mycloud.credentials.storage import save_validate
from mycloud.mycloudapi.auth.bearer_token import open_for_cert
from mycloud.commands.shared import container


@click.group(name='auth')
def auth_command():
    pass


@auth_command.command()
@Halo(text='Saving credentials...', spinner='dots')
# TODO: click.password_option()
def login():
    user = input('Email: ')
    password = getpass.getpass()
    save_validate(user, password)


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
