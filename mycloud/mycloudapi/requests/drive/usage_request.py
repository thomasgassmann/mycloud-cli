import json
import time
from mycloud.mycloudapi.requests import MyCloudRequest, Method


REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/usage?nocache={}'


class UsageRequest(MyCloudRequest):

    def get_method(self):
        return Method.GET

    def get_request_url(self):
        return REQUEST_URL.format(int(time.time()))

    @staticmethod
    def format_response(response):
        json_data = json.loads(response.text)
        return json_data
