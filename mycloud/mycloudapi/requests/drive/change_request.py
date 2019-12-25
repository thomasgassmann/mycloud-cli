import json
import time

from mycloud.mycloudapi.helper import (get_object_id,
                                       raise_if_invalid_drive_path)
from mycloud.mycloudapi.requests import Method, MyCloudRequest

REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/changes/files/?p={}&$limit={}&nocache={}'


class ChangeRequest(MyCloudRequest):

    def __init__(self, object_resource: str, top: int):
        raise_if_invalid_drive_path(object_resource)
        self.object_resource = object_resource
        self.top = top

    def get_method(self):
        return Method.GET

    def get_request_url(self):
        return REQUEST_URL.format(get_object_id(self.object_resource), self.top, int(time.time()))

    @staticmethod
    async def format_response(response):
        text = await response.text()
        json_data = json.loads(text)
        return json_data
