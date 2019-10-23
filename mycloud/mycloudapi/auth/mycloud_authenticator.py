import os
import logging
from enum import Enum
from mycloud.mycloudapi.auth.bearer_token import get_bearer_token
from mycloud.constants import USE_TOKEN_CACHE, TOKEN_CACHE_FOLDER, CACHED_TOKEN_IDENTIFIER


class AuthMode(Enum):
    Password = 0
    Token = 1


class MyCloudAuthenticator:

    def __init__(self):
        self.current_token = None
        self.auth_mode = None
        self.user_name = None
        self.password = None
        self.tried_cached_token = False
        self.token_refresh_required = True
        self.bearer_token = None

    def set_password_auth(self, user_name: str, password: str):
        self.auth_mode = AuthMode.Password
        self.user_name = user_name
        self.password = password
        self.token_refresh_required = True
        self.tried_cached_token = False

    def set_bearer_auth(self, bearer_token):
        self.auth_mode = AuthMode.Token
        if bearer_token == CACHED_TOKEN_IDENTIFIER or bearer_token is None:
            success = self._load_cached_token()
            if success:
                self.bearer_token = self.current_token
            else:
                raise ValueError('No cached token available')
        else:
            self.bearer_token = bearer_token

    def invalidate_token(self):
        self.token_refresh_required = True

    async def get_token(self):
        if self.auth_mode == AuthMode.Token:
            return self.bearer_token

        if self.auth_mode == AuthMode.Password:
            if self.user_name is None or self.password is None:
                raise ValueError('Username and password needs to be set')

            if self.current_token is None or self.token_refresh_required:
                if USE_TOKEN_CACHE and self._load_cached_token() and not self.tried_cached_token:
                    logging.info('Trying to use cached token...')
                    self.tried_cached_token = True
                    self.token_refresh_required = False
                    return self.current_token

                self.current_token = await get_bearer_token(
                    self.user_name, self.password, headless=True)
                if USE_TOKEN_CACHE:
                    self.tried_cached_token = False
                    self._save_token()
                self.token_refresh_required = False
            return self.current_token

        raise ValueError('Invalid auth mode')

    def _load_cached_token(self):
        token_file = self._get_token_file_path()
        if os.path.isfile(token_file):
            self.current_token = open(token_file, 'r').read()
            return True
        return False

    def _save_token(self):
        if not os.path.isdir(TOKEN_CACHE_FOLDER):
            os.makedirs(TOKEN_CACHE_FOLDER)
        token_file = self._get_token_file_path()
        with open(token_file, 'w') as file_stream:
            file_stream.write(self.current_token)

    @staticmethod
    def _get_token_file_path():
        return os.path.join(TOKEN_CACHE_FOLDER, 'token')
