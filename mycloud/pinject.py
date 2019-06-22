import pinject
from click.exceptions import ClickException
from mycloud.credentials.storage import get_credentials
from mycloud.mycloudapi.auth import MyCloudAuthenticator
from mycloud.mycloudapi import MyCloudRequestExecutor


class InstanceBindingSpec(pinject.BindingSpec):

    def __init__(self, name, instance):
        self._name = name
        self._instance = instance

    def configure(self, bind):
        bind(self._name, to_instance=self._instance)


def build_container(**kwargs):
    authenticator = _construct_authenticator(kwargs['token'])
    return pinject.new_object_graph(binding_specs=[
        InstanceBindingSpec('mycloud_request_executor',
                            MyCloudRequestExecutor(authenticator)),
        InstanceBindingSpec('mycloud_authenticator', authenticator)
    ])


def _construct_authenticator(bearer: str):
    authenticator = MyCloudAuthenticator()
    if bearer is not None:
        authenticator.set_bearer_auth(bearer)
    else:
        username, password = get_credentials()
        if not username or not password:
            raise ClickException(
                'Run "mycloud auth login" to authenticate yourself first, or specify a token')
        authenticator.set_password_auth(username, password)
    return authenticator
