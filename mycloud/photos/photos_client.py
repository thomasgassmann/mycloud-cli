import inject

from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.mycloudapi.requests.photos import AddPhotoRequest


class PhotosClient:

    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def add(self, name: str, generator):
        req = AddPhotoRequest(name, generator)
        res = await self.request_executor.execute(req)
        print(res)
