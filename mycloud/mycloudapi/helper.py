import base64


def get_object_id(string: str):
    base_64 = base64.b64encode(string.encode())
    return str(base_64, 'utf-8')


def raise_if_invalid_drive_path(path: str):
    if not path.startswith('/Drive/'):
        raise ValueError('Object path for myCloud must start with /Drive')
