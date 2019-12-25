import io
import logging
from time import sleep

import aiohttp
from requests.models import PreparedRequest

from mycloud.constants import RESET_SESSION_EVERY, WAIT_TIME_MULTIPLIER
from mycloud.mycloudapi.auth import AuthMode, MyCloudAuthenticator
from mycloud.mycloudapi.requests import ContentType, Method, MyCloudRequest
from mycloud.mycloudapi.response import MyCloudResponse
from mycloud.mycloudapi.helper import generator_to_stream


class MyCloudRequestExecutor:

    def __init__(self, mycloud_authenticator: MyCloudAuthenticator):
        self.authenticator = mycloud_authenticator

    async def execute(self, request: MyCloudRequest) -> MyCloudResponse:
        auth_token = await self.authenticator.get_token()

        logging.info(f'Executing request {request}')

        headers = MyCloudRequestExecutor._get_headers(
            request.get_content_type(), auth_token)

        async with aiohttp.ClientSession(headers=headers) as session:
            request_url = MyCloudRequestExecutor._get_request_url(
                request, auth_token)

            method = request.get_method()
            response: aiohttp.ClientResponse = None
            if method == Method.GET:
                response = await MyCloudRequestExecutor._execute_get(session, request, request_url)
            elif method == Method.PUT:
                response = await MyCloudRequestExecutor._execute_put(session, request, request_url)
            elif method == Method.DELETE:
                response = await MyCloudRequestExecutor._execute_delete(session, request_url)
            else:
                raise ValueError(f'Request contains invalid method {method}')

            logging.debug(f'Received status code {response.status}')

            if self._check_retry(response):
                return await self.execute(request)

            mycloud_response = MyCloudResponse(request, response)
            return mycloud_response

    @staticmethod
    async def _execute_get(session: aiohttp.ClientSession, request: MyCloudRequest, request_url: str):
        if request.get_data_generator() is not None:
            raise ValueError('Cannot use data generator with GET request')
        return await session.get(request_url)

    @staticmethod
    async def _execute_put(session: aiohttp.ClientSession, request: MyCloudRequest, request_url: str):
        generator = request.get_data_generator()
        if generator:
            stream = generator_to_stream(generator)
            logging.debug(f'Executing put request with generator...')
            return await session.put(request_url, data=stream)
        return await session.put(request_url)

    @staticmethod
    async def _execute_delete(session: aiohttp.ClientSession, request_url: str):
        return await session.delete(request_url)

    @staticmethod
    def _get_request_url(request: MyCloudRequest, auth_token: str) -> str:
        request_url = request.get_request_url()
        if request.is_query_parameter_access_token():
            req = PreparedRequest()
            req.prepare_url(request_url, {'access_token': auth_token})
            request_url = req.url
        return request_url

    @staticmethod
    def _get_headers(content_type: ContentType, bearer_token: str):
        headers = requests.utils.default_headers()
        headers['Content-Type'] = content_type
        headers['Authorization'] = 'Bearer ' + bearer_token
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        return headers

    def _check_retry(self, response):
        retry = False
        if response.status == 401:
            if self.authenticator.auth_mode == AuthMode.Token:
                raise ValueError('Bearer token is invalid')

            self.authenticator.invalidate_token()
            retry = True

        return retry
