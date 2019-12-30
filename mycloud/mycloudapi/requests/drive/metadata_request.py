import json
import logging

from mycloud.mycloudapi.helper import (get_object_id,
                                       raise_if_invalid_drive_path)
from mycloud.mycloudapi.requests import Method, MyCloudRequest

REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/metadata?p='


class MetadataRequest(MyCloudRequest):
    def __init__(self, object_resource: str):
        if not object_resource.endswith('/'):
            object_resource += '/'
        raise_if_invalid_drive_path(object_resource)
        self.object_resource = object_resource

    def get_method(self):
        return Method.GET

    def get_request_url(self):
        resource = get_object_id(self.object_resource)
        return REQUEST_URL + resource

    def is_query_parameter_access_token(self):
        return True

    @staticmethod
    async def format_response(response):
        if response.status == 404:
            return ([], [])
        logging.debug(f'Awaiting response text...')
        text = await response.text()
        logging.debug(f'Got response text with length {len(text)}')
        json_data = json.loads(text)
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
