import click
import getpass
from mycloud.credentials.storage import save_validate

@click.group(name='auth')
def auth_command():
    pass


@auth_command.command()
def login():
    user = input('Email: ')
    password = getpass.getpass()
    save_validate(user, password)
