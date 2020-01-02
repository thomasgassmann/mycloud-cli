from mycloud.common.functions import get_string_generator
from mycloud.common.operation_timeout import (TimeoutException,
                                              operation_timeout)
from mycloud.common.sha256_file import sha256_file
from mycloud.common.exceptions import MyCloudException
from mycloud.common.urls import merge_url_query_params


def is_int(string: str):
    try:
        int(string)
        return True
    except ValueError:
        return False
