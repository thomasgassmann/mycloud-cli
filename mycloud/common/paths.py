DRIVE_BASE = '/Drive'


def sanitize_path(path: str, force_dir=False, force_file=False) -> str:
    res = DRIVE_BASE + path
    if force_dir:
        return res + '/' if not res.endswith('/') else res

    if force_file:
        return res[:-1] if res.endswith('/') else res

    return res


def unsanitize_path(path: str):
    if not path.startswith(DRIVE_BASE):
        raise ValueError(path)
    return path[len(DRIVE_BASE):]
