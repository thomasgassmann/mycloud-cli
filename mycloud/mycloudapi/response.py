from mycloud.mycloudapi.requests.request import MyCloudRequest


class MyCloudResponse:

    def __init__(self, request: MyCloudRequest, result):
        self.request = request
        self._result = result

    @property
    def success(self) -> bool:
        raise NotImplementedError()

    @property
    def result(self):
        raise NotImplementedError()
