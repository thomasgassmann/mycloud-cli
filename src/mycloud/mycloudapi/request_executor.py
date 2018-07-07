import requests
from logger import log
from requests.models import PreparedRequest
from mycloudapi.auth import MyCloudAuthenticator, AuthMode
from mycloudapi import MyCloudRequest
from mycloudapi.request import Method


class MyCloudRequestExecutor:
    def __init__(self, authenticator: MyCloudAuthenticator):
        self.authenticator = authenticator

    
    def execute_request(self, request: MyCloudRequest):
        content_type = request.get_content_type()
        token = self.authenticator.get_token()
        headers = self._get_headers(content_type, token)
        request_url = request.get_request_url()
        request_method = request.get_method()
        data_generator = request.get_data_generator()
        if request.is_query_parameter_access_token():
            req = PreparedRequest()
            req.prepare_url(request_url, {'access_token': token})
            request_url = req.url
            
        if request_method == Method.GET:
            if data_generator:
                raise ValueError('Cannot have a data generator for HTTP GET')
            response = requests.get(request_url)
        elif request_method == Method.PUT:
            response = requests.put(request_url, headers=headers) if not data_generator else requests.put(url, headers=headers, data=data_generator)
        else:
            raise ValueError('Invalid request method')
        ignore_not_found = request.ignore_not_found()
        retry = self._check_validity(response, ignore_not_found)
        if retry:
            return self.execute_request(request)
        return response


    def _get_headers(self, content_type: str, bearer_token: str):
        headers = {
            'Content-Type': content_type,
            'Authorization': 'Bearer ' + bearer_token
        }
        return headers

    
    def _check_validity(self, response, ignore_not_found):
        log(f'Checking status code (Status {str(response.status_code)})...')
        if response.status_code == 404 and not ignore_not_found:
            raise ValueError('File not found in myCloud')

        retry = False
        if response.status_code == 401:
            if self.authenticator.auth_mode == AuthMode.Token:
                raise ValueError('Bearer token is invalid')
            else:
                self.authenticator.invalidate_token()
                retry = True

        if not str(response.status_code).startswith('2') and response.status_code != 404 and response.status_code != 401:
            log(f'ERR: Status code {str(response.status_code)}!')
            log(f'ERR: {str(response.content)}')
            raise ValueError('Error while performing myCloud request')
        return retry