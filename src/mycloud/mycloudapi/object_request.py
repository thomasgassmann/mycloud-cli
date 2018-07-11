import requests, base64, os
from mycloudapi.request import MyCloudRequest, Method, ContentType
from mycloudapi.helper import get_object_id, raise_if_invalid_cloud_path


REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/object?p='


class ObjectRequest(MyCloudRequest):

    def __init__(self, object_resource: str):
        raise_if_invalid_cloud_path(object_resource)
        self.object_resource = object_resource

    
    def get_request_url(self):
        return REQUEST_URL + get_object_id(self.object_resource)


class PutObjectRequest(ObjectRequest):

    def __init__(self, object_resource: str, generator):
        super().__init__(object_resource)
        self.generator = generator


    def get_method(self) -> Method:
        return Method.PUT

    
    def get_data_generator(self):
        return self.generator

    
    def get_content_type(self) -> str:
        return ContentType.APPLICATION_OCTET_STREAM


class GetObjectRequest(ObjectRequest):

    def __init__(self, object_resource: str, ignore_bad_request=False):
        super().__init__(object_resource)
        self.ignore_400 = ignore_bad_request


    def get_method(self) -> Method:
        return Method.GET

    
    def ignore_bad_request(self):
        return self.ignore_400

    
    def is_query_parameter_access_token(self):
        return True