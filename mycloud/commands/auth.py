import click
import getpass
from mycloud.credentials.storage import save_validate
from mycloud.mycloudapi.auth.bearer_token import open_for_cert


@click.group(name='auth')
def auth_command():
    pass


@auth_command.command()
# TODO: click.password_option()
def login():
    user = input('Email: ')
    password = getpass.getpass()
    save_validate(user, password)


@auth_command.command()
def cert():
    open_for_cert()
