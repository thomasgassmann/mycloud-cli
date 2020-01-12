from mycloud.mycloudapi.helper import get_object_id
from mycloud.mycloudapi.requests import Method, MyCloudRequest

REQUEST_URL = 'https://library.prod.mdl.swisscom.ch/v2/photos/assets?p='


class AddPhotoRequest(MyCloudRequest):

    def __init__(self, res: str, generator, filename: str):
        self._res = res
        self._generator = generator
        self._filename = filename

    def get_request_url(self):
        return REQUEST_URL + get_object_id(self._res)

    def get_method(self):
        return Method.PUT

    def get_data_generator(self):
        return self._generator

    def get_additional_headers(self):
        disposition_str = 'attachment'
        if self._filename is not None:
            disposition_str += f'; filename={self._filename}'
        return {
            'Content-Disposition': disposition_str
        }

    @staticmethod
    async def format_response(response):
        print(response.status)
        if response.status == 400:
            text = await response.text()
            print(text)
