from logger import log
from mycloudapi.auth.bearer_token import get_bearer_token
from enum import Enum


class AuthMode(Enum):
    Password = 0
    Token = 1


class MyCloudAuthenticator:

    def __init__(self):
        self.current_token = None


    def set_password_auth(self, user_name, password):
        self.auth_mode = AuthMode.Password
        self.user_name = user_name
        self.password = password
        self.token_refresh_required = True


    def set_bearer_auth(self, bearer_token):
        self.auth_mode = AuthMode.Token
        self.bearer_token = bearer_token

    
    def invalidate_token(self):
        self.token_refresh_required = True


    def get_token(self):
        if self.auth_mode == AuthMode.Token:
            return self.bearer_token
        elif self.auth_mode == AuthMode.Password:
            if self.user_name is None or self.password is None:
                raise ValueError('Username and password needs to be set')

            if self.current_token is None or self.token_refresh_required:
                self.current_token = get_bearer_token(self.user_name, self.password)
                self.token_refresh_required = False
            return self.current_token