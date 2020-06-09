import json
import os
import asyncio
import inject
from wsgidav.wsgidav_app import WsgiDAVApp
from cheroot import wsgi
from mycloud.constants import WEBDAV_CONFIG_LOCATION
from mycloud.credentials import CredentialStorage
from mycloud.webdav.wsgidav.provider import MyCloudWebdavProvider
from mycloud.webdav.client import MyCloudDavClient
from mycloud.mycloudapi.auth import MyCloudAuthenticator


class WebdavServer:

    credentials_storage: CredentialStorage = inject.attr(CredentialStorage)
    authenticator: MyCloudAuthenticator = inject.attr(MyCloudAuthenticator)
    provider: MyCloudWebdavProvider = inject.attr(MyCloudWebdavProvider)
    client: MyCloudDavClient = inject.attr(MyCloudDavClient)

    def __init__(self):
        self._config = json.load(open(WEBDAV_CONFIG_LOCATION))

    def run(self, host, port, validate_credentials, folder_creation_in_cache, file_creation_in_cache):
        self._validate_configure_authenticator(validate_credentials)

        self.client.folder_creation_in_cache = folder_creation_in_cache
        self.client.file_creation_in_cache = file_creation_in_cache

        port = int(port)
        config = {
            "host": host,
            "port": port,
            "provider_mapping": {
                '/': self.provider
            },
            "http_authenticator": {
                "accept_basic": True
            },
            "error_printer": {"catch_all": True},
            "simple_dc": {
                "user_mapping": {
                    "*": {
                        self._config['webDavUser']: {
                            "password": self._config['webDavPassword']
                        }
                    }
                }
            }
        }

        app = WsgiDAVApp(config)
        server_args = {
            "bind_addr": (host, port),
            "wsgi_app": app
        }

        server = wsgi.Server(**server_args)
        server.start()

    def _validate_configure_authenticator(self, validate):
        user = self._config['myCloudUser']
        (user, password) = self.credentials_storage.load_with_user(user)
        if validate:
            valid = asyncio.get_event_loop().run_until_complete(
                self.credentials_storage.validate(user, password))
            if not valid:
                raise PermissionError('Invalid credentials')

        self.authenticator.set_password_auth(user, password)
