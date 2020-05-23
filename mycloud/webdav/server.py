from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.http_authenticator import HTTPAuthenticator
from cheroot import wsgi


class WebdavServer:

    def run(self, host, port):
        port = int(port)
        config = {
            "host": host,
            "port": port,
            "provider_mapping": {
                '/': FilesystemProvider('/tmp')
            },
            "verbose": 1,
            "http_authenticator": {
                "accept_basic": True
            },
            "simple_dc": {
                "user_mapping": {
                    "*": {
                        "thomas": {
                            "password": "test"
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
