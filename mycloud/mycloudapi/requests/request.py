from abc import abstractmethod, ABC
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
        return None

    @abstractmethod
    def get_method(self):
        return None

    @staticmethod
    def is_query_parameter_access_token():
        return False

    @staticmethod
    def ignored_error_status_codes():
        return []

    @staticmethod
    def get_data_generator():
        return None

    @staticmethod
    def get_content_type():
        return ContentType.APPLICATION_JSON
