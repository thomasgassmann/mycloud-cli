import inject

from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.mycloudapi.requests.photos import AddPhotoRequest


class PhotosClient:

    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)

    async def add(self, name: str, generator, filename):
        req = AddPhotoRequest(name, generator, filename)
        res = await self.request_executor.execute(req)
        print(await res.formatted())
