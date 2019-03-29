from time import sleep
import requests
from requests.models import PreparedRequest
from mycloud.logger import log, add_request_count, save_files
from mycloud.mycloudapi.auth import MyCloudAuthenticator, AuthMode
from mycloud.mycloudapi import MyCloudRequest
from mycloud.mycloudapi.request import ContentType
from mycloud.mycloudapi.request import Method
from mycloud.constants import WAIT_TIME_MULTIPLIER, RESET_SESSION_EVERY


class MyCloudRequestExecutor:

    def __init__(self, authenticator: MyCloudAuthenticator):
        self._request_count = 0
        self.wait_time = 10
        self.authenticator = authenticator
        self.session = requests.Session()
        self._reset_wait_time()


    def execute_request(self, request: MyCloudRequest):
        # TODO: also use aiohttp instead of requests
        content_type = request.get_content_type()
        token = self.authenticator.get_token()
        headers = MyCloudRequestExecutor._get_headers(content_type, token)
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
            response = self.session.get(request_url, headers=headers)
        elif request_method == Method.PUT:
            response = self.session.put(request_url, headers=headers) \
                if not data_generator \
                else requests.put(request_url, headers=headers, data=data_generator)
        else:
            raise ValueError('Invalid request method')
        if self._request_count % RESET_SESSION_EVERY == 0:
            self.reset_session()
            save_files()
        self._request_count += 1
        add_request_count(type(request).__name__)
        ignored = request.ignored_error_status_codes()
        retry = self._check_validity(response, ignored, request_url)
        if retry:
            return self.execute_request(request)
        return response


    def reset_session(self):
        self.session.close()
        del self.session
        self.session = requests.Session()


    def _reset_wait_time(self):
        self.wait_time = 10


    @staticmethod
    def _get_headers(content_type: ContentType, bearer_token: str):
        headers = requests.utils.default_headers()
        headers['Content-Type'] = content_type
        headers['Authorization'] = 'Bearer ' + bearer_token
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        return headers


    def _check_validity(self, response, ignored, request_url: str):
        separately_handled = [401, 500, 404, 400, 409, 502]

        retry = False
        if response.status_code == 401:
            if self.authenticator.auth_mode == AuthMode.Token:
                raise ValueError('Bearer token is invalid')

            self.authenticator.invalidate_token()
            retry = True

        if response.status_code == 500 and 500 not in ignored:
            log(f'HTTP {response.status_code} returned from server', error=True)
            log('ERR: {}'.format(str(response.content)), error=True)
            log('Waiting {} seconds until retry...'.format(self.wait_time))
            sleep(self.wait_time)
            retry = True
            # TODO: make logarithmic instead of exponential?
            self.wait_time = int(self.wait_time * WAIT_TIME_MULTIPLIER)
        else:
            self._reset_wait_time()

        log('Checking status code {} (Status {})...'.format(
            request_url, str(response.status_code)))
        if response.status_code == 404 and 404 not in ignored:
            raise ValueError('File not found in myCloud')

        if response.status_code == 400 and 400 not in ignored:
            raise ValueError('Bad Request: {}'.format(response.text))

        if response.status_code == 409 and 409 not in ignored:
            raise ValueError('Conflict: {}'.format(response.text))

        if not str(response.status_code).startswith('2') and \
           response.status_code not in separately_handled:
            log('ERR: Status code {}!'.format(str(response.status_code)))
            log('ERR: {}'.format(str(response.content)))
            raise ValueError('Error while performing myCloud request')
        return retry
