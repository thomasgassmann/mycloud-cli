from mycloud.streamapi import CloudStreamAccessor, CloudStream
from mycloud.mycloudapi import ObjectResourceBuilder
from mycloud.filesystem.file_version import CalculatableVersion
from mycloud.filesystem.translatable_path import TranslatablePath


class VersionedCloudStreamAccessor(CloudStreamAccessor):

    def __init__(self, path: TranslatablePath, version: CalculatableVersion, cloud_stream: CloudStream):
        super().__init__(None, cloud_stream)
        self._version = version
        self._base_path = path
        self._current_version_file_parts = []

    def get_base_path(self):
        versioned_object_resource = ObjectResourceBuilder.combine_cloud_path(
            self._base_path.calculate_remote(), self._version.calculate_version())
        return versioned_object_resource

    def get_accessed_file_parts(self):
        return self._current_version_file_parts

    def get_part_file(self, index: int):
        part_file_path = super().get_part_file(index)
        self._current_version_file_parts.append(part_file_path)
        return part_file_path
