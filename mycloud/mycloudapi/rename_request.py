import json
from mycloud.mycloudapi.request import MyCloudRequest, Method
from mycloud.mycloudapi.object_resource_builder import ObjectResourceBuilder
from mycloud.helper import get_string_generator


REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/commands/rename'


class RenameRequest(MyCloudRequest):
    def __init__(self, source: str, destination: str, is_file: bool):
        self._destination = ObjectResourceBuilder.correct_suffix_sep(
            destination, is_file)
        self._source = ObjectResourceBuilder.correct_suffix_sep(
            source, is_file)

    def get_method(self):
        return Method.PUT

    def get_request_url(self):
        return REQUEST_URL

    def get_data_generator(self):
        req = {
            'Source': self._source,
            'Destination': self._destination
        }

        req_json = json.dumps(req)
        return get_string_generator(req_json)
