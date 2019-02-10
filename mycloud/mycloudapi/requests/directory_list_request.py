import json
from enum import Enum
from time import time
from mycloud.mycloudapi.helper import get_object_id, raise_if_invalid_cloud_path
from mycloud.mycloudapi.request import MyCloudRequest, Method


REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/sync/list?p={}&$type={}&nocache={}'


class ListType(Enum):
    Directory = 0
    File = 1
    Both = 2


class DirectoryListRequest(MyCloudRequest):

    def __init__(self, object_resource: str, list_type: ListType, ignore_not_found=False, ignore_internal_server_error=False):
        if not object_resource.endswith('/'):
            object_resource += '/'
        raise_if_invalid_cloud_path(object_resource)
        self._object_resource = object_resource
        self._ignore_404 = ignore_not_found
        self._ignore_500 = ignore_internal_server_error
        self._list_type = list_type

    def ignored_error_status_codes(self):
        ignored = []
        if self._ignore_404:
            ignored.append(404)
        if self._ignore_500:
            ignored.append(500)
        return ignored

    def get_method(self):
        return Method.GET

    def get_request_url(self):
        resource = get_object_id(self._object_resource)
        list_type = None
        if self._list_type == ListType.Directory:
            list_type = 'directory'
        elif self._list_type == ListType.File:
            list_type = 'file'
        elif self._list_type == ListType.Both:
            list_type = 'file,directory'
        else:
            raise ValueError('List type could not be found')
        unix_time = int(time())
        return REQUEST_URL.format(resource, list_type, unix_time)

    @staticmethod
    def format_response(response):
        if response.status_code == 404:
            if not self._ignore_404:
                raise ConnectionError('404')
            return []
        return DirectoryListRequest._json_generator(response.text)

    @staticmethod
    def is_timeout(response):
        if response is None:
            return False
        TIMEOUT = 'Operation exceeded time limit.'
        ERROR_KEY = 'error'
        if TIMEOUT not in response.text:
            return False

        error_dic = json.loads(response.text)
        if response.status_code != 500 or ERROR_KEY not in error_dic:
            return False

        return TIMEOUT in error_dic[ERROR_KEY]

    @staticmethod
    def _json_generator(string: str):
        loaded = json.loads(string)
        for item in loaded:
            yield item
