import os
from pathlib import Path
from mycloud.helper import is_int
from mycloud.mycloudapi import MyCloudRequestExecutor, MetadataRequest
from mycloud.streamapi import (
    UpStream,
    DownStream,
    UpStreamExecutor,
    DownStreamExecutor,
    ProgressReporter,
    CloudStream
)
from mycloud.streamapi.transforms import StreamTransform
from mycloud.filesystem.translatable_path import TranslatablePath, BasicRemotePath
from mycloud.filesystem.file_version import CalculatableVersion
from mycloud.filesystem.versioned_stream_accessor import VersionedCloudStreamAccessor
from mycloud.filesystem.metadata_manager import MetadataManager
from mycloud.filesystem.file_metadata import FileMetadata, Version
from mycloud.constants import METADATA_FILE_NAME


class FileManager:

    def __init__(self, request_executor: MyCloudRequestExecutor, transforms: List[StreamTransform], reporter: ProgressReporter):
        self._request_executor = request_executor
        self._transforms = transforms
        self._metadata_manager = MetadataManager(request_executor)
        self._reporter = ProgressReporter() if reporter is None else reporter

    def read_directory(self,
                       translatable_path: TranslatablePath,
                       recursive=False,
                       **kwargs):
        base = translatable_path.calculate_remote()
        metadata_request = MetadataRequest(base, ignore_not_found=True)
        response = self._request_executor.execute_request(metadata_request)
        if response.status_code = 404:
            yield from []
        (dirs, files) = MetadataRequest.format_response(response)
        if len(files) == 1 and files[0]['Name'] == METADATA_FILE_NAME:
            yield translatable_path
        if recursive:
            for dir in dirs:
                remote_path = BasicRemotePath(dir)
                yield from self.read_directory(translatable_path, True)
        elif not bool(kwargs['second']):
            yield from self.read_directory(translatable_path, False, second=True)

    def read_file(self,
                  downstream: DownStream,
                  translatable_path: TranslatablePath,
                  calculatable_version: CalculatableVersion):
        metadata = self._metadata_manager.get_metadata(translatable_path)
        calculated_version = calculatable_version.calculate_version()
        if not metadata.contains_version(calculated_version):
            raise ValueError('Version does not exist for given file')

        versioned_stream_accessor = self._prepare_versioned_stream(
            translatable_path, calculatable_version, upstream)
        downstreamer = DownStreamExecutor(
            self._request_executor, self._reporter)
        downstreamer.download_stream(versioned_stream_accessor)

    def read_file_metadata(self,
                           translatable_path: TranslatablePath):
        metadata = self._metadata_manager.get_metadata(translatable_path)
        return metadata

    def write_file(self,
                   upstream: UpStream,
                   translatable_path: TranslatablePath,
                   calculatable_version: CalculatableVersion):
        existing_metadata = self._metadata_manager.get_metadata(
            translatable_path)
        existing_metadata = existing_metadata if existing_metadata is not None else FileMetadata()
        version_identifier = calculatable_version.calculate_version()

        if existing_metadata.contains_version(version_identifier):
            raise ValueError('Version does already exist')

        versioned_stream_accessor = self._prepare_versioned_stream(
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

    def _prepare_versioned_stream(self, translatable_path: TranslatablePath, calculatable_version: CalculatableVersion, cloud_stream: CloudStream):
        versioned_cloud_stream_accessor = VersionedCloudStreamAccessor(
            translatable_path, version, cloud_stream)
        for transform in self._transforms:
            versioned_cloud_stream_accessor.add_transform(transform)
        return versioned_cloud_stream_accessor
