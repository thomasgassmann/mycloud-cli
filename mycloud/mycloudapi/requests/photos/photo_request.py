from mycloud.mycloudapi.helper import get_object_id
from mycloud.mycloudapi.requests import Method, MyCloudRequest

REQUEST_URL = 'https://library.prod.mdl.swisscom.ch/v2/photos/assets?p='


class AddPhotoRequest(MyCloudRequest):

    def __init__(self, res: str, generator):
        self._res = res
        self._generator = generator

    def get_request_url(self):
        return REQUEST_URL + get_object_id(self._res)

    def get_method(self):
        return Method.PUT

    def get_data_generator(self):
        return self._generator
