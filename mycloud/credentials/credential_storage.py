import json
import keyring
from mycloud.constants import AUTHENTICATION_INFO_LOCATION, SERVICE_NAME
from mycloud.mycloudapi.auth import get_bearer_token
from mycloud.logger import log


def save_validate(user_name: str, password: str):
    if not _validate_credentials(user_name, password):
        log('Invalid credentials provided! Aborting...')
        return

    with open(AUTHENTICATION_INFO_LOCATION, 'w') as file:
        json.dump({
            'user': user_name
        }, file)
    keyring.set_password(SERVICE_NAME, user_name, password)


def get_credentials():
    with open(AUTHENTICATION_INFO_LOCATION, 'r') as file:
        auth_info = json.load(file)
    password = keyring.get_password(SERVICE_NAME, auth_info['user'])
    return (auth_info['user'], password)


def _validate_credentials(user_name: str, password: str) -> bool:
    try:
        get_bearer_token(user_name, password)
        return True
    except ValueError:
        return False
