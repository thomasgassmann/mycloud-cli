from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder
from mycloud.mycloudapi.requests.drive import PutObjectRequest, GetObjectRequest
from mycloud.filesystem.file_metadata import FileMetadata
from mycloud.filesystem.translatable_path import TranslatablePath
from mycloud.constants import METADATA_FILE_NAME
from mycloud.common import get_string_generator


class MetadataManager:

    def __init__(self, request_executor: MyCloudRequestExecutor):
        self._request_executor = request_executor

    async def get_metadata(self, path: TranslatablePath):
        metadata_path = MetadataManager._get_metadata_path(path)
        get_request = GetObjectRequest(metadata_path, ignore_not_found=True)
        response = await self._request_executor.execute_request(get_request)
        return None if response.status_code == 404 else FileMetadata.from_json(response.text)

    async def update_metadata(self, path: TranslatablePath, metadata: FileMetadata):
        metadata_path = MetadataManager._get_metadata_path(path)
        json_representation = FileMetadata.to_json(metadata)
        byte_generator = get_string_generator(json_representation)
        put_request = PutObjectRequest(metadata_path, byte_generator)
        _ = await self._request_executor.execute_request(put_request)

    @staticmethod
    def _get_metadata_path(path: TranslatablePath):
        full_path = path.calculate_remote()
        metadata_path = ObjectResourceBuilder.combine_cloud_path(
            full_path, METADATA_FILE_NAME)
        return metadata_path
