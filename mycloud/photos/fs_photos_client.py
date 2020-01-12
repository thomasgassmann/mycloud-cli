import inject
import os
from mycloud.common import to_generator
from mycloud.photos.photos_client import PhotosClient


class FsPhotosClient:

    photos_client: PhotosClient = inject.attr(PhotosClient)

    async def add(self, local_path, name):
        filename = os.path.basename(local_path)

        with open(local_path, 'rb') as f:
            generator = to_generator(f)
            await self.photos_client.add(name, generator, filename)
