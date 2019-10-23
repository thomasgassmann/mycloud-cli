import os
import json
import logging
import keyring
import asyncio
from mycloud.constants import AUTHENTICATION_INFO_LOCATION, SERVICE_NAME
from mycloud.mycloudapi.auth import get_bearer_token


class CredentialStorage:

    def __init__(self):
        pass

    @classmethod
    async def save(cls, username: str, password: str, skip_validation: bool = False, no_headless_validation: bool = False) -> bool:
        validation_result = True if skip_validation else await _validate_credentials(username, password, not no_headless_validation)
        if not validation_result:
            return False

        with open(AUTHENTICATION_INFO_LOCATION, 'w') as file:
            json.dump({
                'user': username
            }, file)
        keyring.set_password(SERVICE_NAME, username, password)
        return True

    @classmethod
    def load(cls):
        if not os.path.isfile(AUTHENTICATION_INFO_LOCATION):
            return None, None
        with open(AUTHENTICATION_INFO_LOCATION, 'r') as file:
            auth_info = json.load(file)
        password = keyring.get_password(SERVICE_NAME, auth_info['user'])
        return (auth_info['user'], password)


async def _validate_credentials(user_name: str, password: str, headless: bool) -> bool:
    try:
        await get_bearer_token(user_name, password, headless)
        return True
    except ValueError:
        return False
