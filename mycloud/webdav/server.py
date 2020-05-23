from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.http_authenticator import HTTPAuthenticator
from wsgidav.dir_browser import WsgiDavDirBrowser
from wsgidav.debug_filter import WsgiDavDebugFilter
from wsgidav.error_printer import ErrorPrinter
from wsgidav.request_resolver import RequestResolver
from cheroot import wsgi

from mycloud.webdav.wsgidav import MyCloudDomainController


class WebdavServer:

    def run(self, host, port):
        port = int(port)
        config = {
            "middleware_stack": [
                WsgiDavDebugFilter,
                ErrorPrinter,
                HTTPAuthenticator,
                WsgiDavDirBrowser,
                RequestResolver
            ],
            "host": host,
            "port": port,
            "provider_mapping": {
                '/': FilesystemProvider('/tmp')
            },
            "verbose": 5,
            "http_authenticator": {
                "accept_basic": True,
                "domain_controller": MyCloudDomainController
            },
            "enable_loggers": ["lock_manager", "property_manager", "http_authenticator"],
            "error_printer": {"catch_all": True}
        }

        app = WsgiDAVApp(config)
        server_args = {
            "bind_addr": (host, port),
            "wsgi_app": app
        }

        server = wsgi.Server(**server_args)
        server.start()
