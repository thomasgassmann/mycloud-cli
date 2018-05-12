import base64
from logger import log


class MyCloudRequest:
    def __init__(self, object_resource: str, bearer_token: str):
        if not object_resource.startswith('/Drive/'):
            raise ValueError('Object path for myCloud must start with /Drive')
        self.object = object_resource
        self.bearer_token = bearer_token
    

    def raise_if_invalid(self, response, ignore_not_found=False):
        log(f'Checking status code for response resource {self.object} (Status {str(response.status_code)})...')
        if response.status_code == 404 and not ignore_not_found:
            raise ValueError('File not found in myCloud')

        if response.status_code == 401:
            raise ValueError('Bearer token is invalid')

        if not str(response.status_code).startswith('2') and response.status_code != 404 and response.status_code != 401:
            log(f'ERR: Status code {str(response.status_code)}!')
            log('ERR: CONTENT:')
            log(f'ERR: {str(response.content)}')
            raise ValueError('Error while performing myCloud request')


    def get_object_id(self):
        base_64 = base64.b64encode(self.object.encode())
        return str(base_64, 'utf-8')


    def get_headers(self, content_type: str):
        headers = {
            'Content-Type': content_type,
            'Authorization': 'Bearer ' + self.bearer_token
        }
        return headers