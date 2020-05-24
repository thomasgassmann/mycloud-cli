import json
import os
import asyncio
import inject
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.http_authenticator import HTTPAuthenticator
from wsgidav.dir_browser import WsgiDavDirBrowser
from wsgidav.debug_filter import WsgiDavDebugFilter
from wsgidav.error_printer import ErrorPrinter
from wsgidav.request_resolver import RequestResolver
from cheroot import wsgi
from mycloud.constants import WEBDAV_CONFIG_LOCATION
from mycloud.credentials import CredentialStorage


class WebdavServer:

    credentials_storage: CredentialStorage = inject.attr(CredentialStorage)

    def __init__(self):
        self._config = json.load(open(WEBDAV_CONFIG_LOCATION))

    def run(self, host, port):
        self._validate_get_user()

        port = int(port)
        config = {
            "host": host,
            "port": port,
            "provider_mapping": {
                '/': FilesystemProvider('/tmp')
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

    def _validate_get_user(self):
        user = self._config['myCloudUser']
        (user, password) = self.credentials_storage.load_with_user(user)
        valid = asyncio.get_event_loop().run_until_complete(
            self.credentials_storage.validate(user, password))
        if not valid:
            raise PermissionError('Invalid credentials')
