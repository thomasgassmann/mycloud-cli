from mycloud.common.directory_list import get_all_files
from mycloud.common.functions import get_string_generator
from mycloud.common.operation_timeout import (TimeoutException,
                                              operation_timeout)
from mycloud.common.sha256_file import sha256_file


def is_int(string: str):
    try:
        int(string)
        return True
    except ValueError:
        return False


def to_unix_timestamp(ticks):
    return (ticks - 621355968000000000) / 10000000
