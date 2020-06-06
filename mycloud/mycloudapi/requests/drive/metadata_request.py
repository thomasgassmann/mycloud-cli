import json
import logging
import time
from datetime import datetime
from typing import List
from dataclasses import dataclass

from mycloud.mycloudapi.helper import get_object_id
from mycloud.mycloudapi.requests import Method, MyCloudRequest
from mycloud.common import parse_datetime, unsanitize_path, sanitize_path

REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/metadata?p={0}&nocache={1}'


@dataclass
class DirEntry:
    creation_time: datetime
    modification_time: datetime
    name: str
    path: str


@dataclass
class FileEntry:
    creation_time: datetime
    etag: str
    extension: str
    length: int
    mime: str
    modification_time: datetime
    name: str
    path: str


@dataclass
class MyCloudMetadata:
    dirs: List[DirEntry]
    files: List[FileEntry]
    modification_time: datetime
    creation_time: datetime
    name: str
    path: str


class MetadataRequest(MyCloudRequest):
    def __init__(self, object_resource: str):
        logging.debug(f'Metadata request {object_resource}')
        object_resource = sanitize_path(object_resource, force_dir=True)
        self.object_resource = object_resource

    def get_method(self):
        return Method.GET

    def get_request_url(self):
        resource = get_object_id(self.object_resource)
        return REQUEST_URL.format(resource, int(time.time()))

    def is_query_parameter_access_token(self):
        return True

    @staticmethod
    async def format_response(response):
        if response.status == 404:
            return None
        logging.debug(f'Awaiting response text...')
        text = await response.text()
        logging.debug(f'Got response text with length {len(text)}')
        json_data = json.loads(text)
        files = MetadataRequest._get_files(json_data)
        dirs = MetadataRequest._get_directories(json_data)
        logging.debug(
            f'Formatted response ({len(files)} files, {len(dirs)} dirs)')
        return MyCloudMetadata(
            dirs=dirs,
            files=files,
            modification_time=parse_datetime(json_data['ModificationTime']),
            creation_time=parse_datetime(json_data['CreationTime']),
            name=json_data['Name'],
            path=unsanitize_path(json_data['Path']))

    @staticmethod
    def _get_files(json_content):
        if 'Files' in json_content:
            files = json_content['Files']
            return list(map(lambda x: FileEntry(
                creation_time=parse_datetime(x['CreationTime']),
                etag=x['ETag'],
                extension=x['Extension'],
                length=x['Length'],
                mime=x['Mime'],
                modification_time=parse_datetime(x['ModificationTime']),
                name=x['Name'],
                path=unsanitize_path(x['Path'])), files))
        return []

    @staticmethod
    def _get_directories(json_content):
        if 'Directories' in json_content:
            directories = json_content['Directories']
            return list(map(lambda x: DirEntry(
                creation_time=parse_datetime(x['CreationTime']),
                modification_time=parse_datetime(x['ModificationTime']),
                name=x['Name'],
                path=unsanitize_path(x['Path'])), directories))
        return []
