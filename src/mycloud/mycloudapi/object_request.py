import requests, base64, os
import mycloudapi.request as request


REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/object?p='


class ObjectRequest(request.MyCloudRequest):
    def __init__(self, object_resource: str, bearer_token: str):
        super().__init__(object_resource, bearer_token)


    def put(self, generator):
        headers = super(ObjectRequest, self).get_headers('application/octet-stream')
        obj_id = super(ObjectRequest, self).get_object_id()
        if generator is not None:
            r = requests.put(REQUEST_URL + obj_id, headers=headers, data=generator)
        else:
            r = requests.put(REQUEST_URL + obj_id, headers=headers)
        super(ObjectRequest, self).raise_if_invalid(r)


    def get(self):
        obj_id = super(ObjectRequest, self).get_object_id()
        request_url = REQUEST_URL + obj_id + '&access_token=' + self.bearer_token
        response = requests.get(request_url)
        super(ObjectRequest, self).raise_if_invalid(response)
        return response