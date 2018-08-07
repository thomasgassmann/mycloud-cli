from mycloud.logger import log
from abc import abstractmethod, ABC
from enum import Enum


BASE_URL = 'https://storage.prod.mdl.swisscom.ch/'


class ContentType(Enum):
    APPLICATION_JSON = 'application/json'
    APPLICATION_OCTET_STREAM = 'application/octet-stream'


class Method(Enum):
    GET = 0
    PUT = 1


class MyCloudRequest(ABC):

    @abstractmethod
    def get_request_url(self):
        return None

    @abstractmethod
    def get_method(self):
        return None

    def is_query_parameter_access_token(self):
        return False

    def ignore_not_found(self):
        return False

    def ignore_bad_request(self):
        return False

    def get_data_generator(self):
        return None

    def get_content_type(self):
        return ContentType.APPLICATION_JSON
