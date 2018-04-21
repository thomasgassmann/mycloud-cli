import os, requests, json
import mycloudapi.request as request


'https://www.swisscom.ch/login/'
REQUEST_URL = 'https://storage.prod.mdl.swisscom.ch/metadata?p='


class MetadataRequest(request.MyCloudRequest):
    def __init__(self, object_resource: str, bearer_token: str):
        super().__init__(object_resource, bearer_token)
        if not self.object.endswith('/'):
            raise ValueError('Cannot list a file')


    def get_contents(self, ignore_not_found=False):
        headers = super(MetadataRequest, self).get_headers('application/json')
        url = REQUEST_URL + super(MetadataRequest, self).get_object_id()
        response = requests.get(url, headers=headers)
        super(MetadataRequest, self).raise_if_invalid(response, ignore_not_found)
        if response.status_code == 404:
            return ([], [])
        json_data = json.loads(response.text)
        files = MetadataRequest.__get_files(json_data)
        dirs = MetadataRequest.__get_directories(json_data)
        return (dirs, files)

    
    @staticmethod
    def __get_files(json):
        if 'Files' in json:
            files = json['Files']
            return files
        return []


    @staticmethod
    def __get_directories(json):
        if 'Directories' in json:
            directories = json['Directories']
            return directories
        return []