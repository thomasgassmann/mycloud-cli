from mycloud.mycloudapi.requests.request import MyCloudRequest


class MyCloudResponse:

    def __init__(self, request: MyCloudRequest):
        self.request = request
