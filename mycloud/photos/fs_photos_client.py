import inject
from mycloud.photos.photos_client import PhotosClient


class FsPhotosClient:

    photos_client: PhotosClient = inject.attr(PhotosClient)

    async def add(self, local_path, name):
        with open(local_path, 'rb') as f:
            await self.photos_client.add(name, f)
