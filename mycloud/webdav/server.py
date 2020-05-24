import json
import os
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.http_authenticator import HTTPAuthenticator
from wsgidav.dir_browser import WsgiDavDirBrowser
from wsgidav.debug_filter import WsgiDavDebugFilter
from wsgidav.error_printer import ErrorPrinter
from wsgidav.request_resolver import RequestResolver
from cheroot import wsgi
from mycloud.constants import WEBDAV_CONFIG_LOCATION


class WebdavServer:

    def __init__(self):
        self._config = json.load(open(WEBDAV_CONFIG_LOCATION))

    def run(self, host, port):
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
                    "*": self._config['users']
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
