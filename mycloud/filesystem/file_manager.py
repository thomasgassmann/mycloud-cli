import os
from pathlib import Path
from mycloud.helper import is_int
from mycloud.mycloudapi import MyCloudRequestExecutor, MetadataRequest
from mycloud.streamapi import (
    UpStream,
    DownStream,
    UpStreamExecutor,
    DownStreamExecutor,
    ProgressReporter
)
from mycloud.streamapi.transforms import StreamTransform
from mycloud.filesystem.translatable_path import TranslatablePath
from mycloud.filesystem.file_version import CalculatableVersion
from mycloud.filesystem.versioned_stream_accessor import VersionedCloudStreamAccessor
from mycloud.filesystem.metadata_manager import MetadataManager
from mycloud.filesystem.file_metadata import FileMetadata, Version


class FileManager:

    def __init__(self, request_executor: MyCloudRequestExecutor, transforms: List[StreamTransform], reporter: ProgressReporter):
        self._request_executor = request_executor
        self._transforms = transforms
        self._metadata_manager = MetadataManager(request_executor)
        self._reporter = ProgressReporter() if reporter is None else reporter

    def read_directory(self,
                       translatable_path: TranslatablePath,
                       recursive=False):
        # Returns a list of translatable paths?
        pass

    def read_file(self,
                  downstream: DownStream,
                  translatable_path: TranslatablePath,
                  calculatable_version: CalculatableVersion):
        pass

    def read_file_metadata(self,
                           translatable_path: TranslatablePath):
        pass

    def write_file(self,
                   upstream: UpStream,
                   translatable_path: TranslatablePath,
                   calculatable_version: CalculatableVersion):
        existing_metadata = self._metadata_manager.get_metadata(
            translatable_path)
        version_identifier = calculatable_version.calculate_version()

        if existing_metadata.contains_version(version_identifier):
            raise ValueError('Version does already exist')

        versioned_stream_accessor = VersionedCloudStreamAccessor(
            translatable_path, calculatable_version, upstream)

        version = Version(version_identifier, remote_base_path)

        if upstream.continued_append_starting_at_part_index > 0:
            versioned_base_path = versioned_stream_accessor.get_base_path()
            list_directory_request = MetadataRequest(
                versioned_base_path, ignore_not_found=True)
            listed_directory = self._request_executor.execute_request(
                list_directory_request)
            (dirs, files) = MetadataRequest.format_response(listed_directory)
            if len(dirs) != 0:
                raise ValueError(
                    'A versioned directory with partial files cannot contain subdirectories')
            if len(files) != upstream.continued_append_starting_at_part_index:
                raise ValueError('Must append at correct position')
            for file in files:
                file_name = os.path.basename(file)
                path = Path(file_name).with_suffix('').stem
                if not is_int(path):
                    raise ValueError('Non-integer indexed part file found')
                version.add_part_file(file)

        upstreamer = UpStreamExecutor(self.request_executor, self._reporter)
        upstreamer.upload_stream(versioned_stream_accessor)

        remote_base_path = translatable_path.calculate_remote()
        for transform in self._transforms:
            version.add_transform(transform.get_name())
        remote_properties = translatable_path.calculate_properties()

        for key in remote_properties:
            version.add_property(key, remote_properties[key])

        for accessed in versioned_stream_accessor.get_accessed_file_parts():
            version.add_part_file(accessed)
        existing_metadata.update_version(version)

        self._metadata_manager.update_metadata(
            translatable_path, existing_metadata)
