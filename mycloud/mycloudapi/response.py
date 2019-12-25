from mycloud.mycloudapi.requests.request import MyCloudRequest


class MyCloudResponse:

    def __init__(self, request: MyCloudRequest, result):
        self.request = request
        self._result = result

    @property
    def result(self):
        return self._result

    async def formatted(self):
        if 'format_response' not in dir(type(self.request)):
            return None

        return await type(self.request).format_response(self.result)
