import inject
from click.exceptions import ClickException
from mycloud.mycloudapi.auth import MyCloudAuthenticator
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.credentials import CredentialStorage


def build_container(**kwargs):
    authenticator = _construct_authenticator(kwargs['token'])
    def _inject_config(binder):
        binder.bind(MyCloudAuthenticator, authenticator)
        binder.bind(MyCloudRequestExecutor, MyCloudRequestExecutor(authenticator))
    inject.configure(_inject_config)


def _construct_authenticator(bearer: str):
    authenticator = MyCloudAuthenticator()
    if bearer is not None:
        authenticator.set_bearer_auth(bearer)
    else:
        username, password = CredentialStorage().load()
        if username and password:
            authenticator.set_password_auth(username, password)

    return authenticator
