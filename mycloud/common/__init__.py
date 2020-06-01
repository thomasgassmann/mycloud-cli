from mycloud.common.abstract_static import abstractstatic
from mycloud.common.exceptions import MyCloudException
from mycloud.common.functions import get_string_generator
from mycloud.common.operation_timeout import (TimeoutException,
                                              operation_timeout)
from mycloud.common.sha256_file import sha256_file
from mycloud.common.urls import merge_url_query_params
from mycloud.common.generator import to_generator
from mycloud.common.sync import run_sync
from mycloud.common.time import parse_datetime, to_unix
from mycloud.common.paths import unsanitize_path, sanitize_path, is_dir


def is_int(string: str):
    try:
        int(string)
        return True
    except ValueError:
        return False
