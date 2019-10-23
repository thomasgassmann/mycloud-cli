import json
import logging
from mycloud.mycloudapi.helper import get_object_id, raise_if_invalid_drive_path
from mycloud.mycloudapi.requests import MyCloudRequest, Method


REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/metadata?p='


class MetadataRequest(MyCloudRequest):
    def __init__(self, object_resource: str, ignore_not_found=False, ignore_bad_request=False):
        if not object_resource.endswith('/'):
            object_resource += '/'
        raise_if_invalid_drive_path(object_resource)
        self.object_resource = object_resource
        self._ignore_404 = ignore_not_found
        self._ignore_400 = ignore_bad_request

    def get_method(self):
        return Method.GET

    def get_request_url(self):
        resource = get_object_id(self.object_resource)
        return REQUEST_URL + resource

    def ignored_error_status_codes(self):
        ignored = []
        if self._ignore_400:
            ignored.append(400)
        if self._ignore_404:
            ignored.append(404)
        return ignored

    def is_query_parameter_access_token(self):
        return True

    @staticmethod
    def format_response(response):
        if response.status_code == 404:
            return ([], [])
        json_data = json.loads(response.text)
        files = MetadataRequest._get_files(json_data)
        dirs = MetadataRequest._get_directories(json_data)
        logging.debug(
            f'Formatted response ({len(files)} files, {len(dirs)} dirs)')
        return (dirs, files)

    @staticmethod
    def _get_files(json_content):
        if 'Files' in json_content:
            files = json_content['Files']
            return files
        return []

    @staticmethod
    def _get_directories(json_content):
        if 'Directories' in json_content:
            directories = json_content['Directories']
            return directories
        return []
