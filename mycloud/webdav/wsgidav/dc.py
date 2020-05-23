from wsgidav.dc.base_dc import BaseDomainController


class MyCloudDomainController(BaseDomainController):

    def __init__(self, app, config):
        super().__init__(app, config)

    def basic_auth_user(self, realm, user_name, password, environ):
        return True

    def require_authentication(self, realm, environ):
        return True

    def get_domain_realm(self, path_info, environ):
        return 'mycloud'

    def supports_http_digest_auth(self):
        return True
