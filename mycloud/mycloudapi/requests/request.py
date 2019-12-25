from abc import ABC, abstractmethod
from enum import Enum


class ContentType:
    APPLICATION_JSON = 'application/json'
    APPLICATION_OCTET_STREAM = 'application/octet-stream'


class Method(Enum):
    GET = 0
    PUT = 1
    DELETE = 2


class MyCloudRequest(ABC):

    @abstractmethod
    def get_request_url(self):
        raise NotImplementedError()

    @abstractmethod
    def get_method(self):
        raise NotImplementedError()

    def is_query_parameter_access_token(self):
        return False

    def get_data_generator(self):
        return None

    def get_content_type(self):
        return ContentType.APPLICATION_JSON
