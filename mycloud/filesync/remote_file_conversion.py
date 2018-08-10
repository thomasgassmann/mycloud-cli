import os
import traceback
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder, RenameRequest, MetadataRequest
from mycloud.filesystem import (
    FileManager,
    MetadataManager,
    HashCalculatedVersion,
    BasicStringVersion,
    BasicRemotePath,
    LocalTranslatablePath,
    FileMetadata,
    Version,
    CalculatableVersion,
    TranslatablePath
)
from mycloud.constants import (
    MY_CLOUD_BIG_FILE_CHUNK_SIZE,
    PARTIAL_EXTENSION,
    START_NUMBER_LENGTH,
    DEFAULT_VERSION,
    AES_EXTENSION,
    METADATA_FILE_NAME
)
from mycloud.filesystem.versioned_stream_accessor import VersionedCloudStreamAccessor
from mycloud.streamapi import ProgressReporter
from mycloud.streamapi.transforms import AES256CryptoTransform
from mycloud.helper import get_all_files_recursively, is_int, TimeoutException
from mycloud.logger import log


def convert_remote_files(request_executor: MyCloudRequestExecutor, mycloud_dir: str, local_dir: str):
    resource_builder = ObjectResourceBuilder(local_dir, mycloud_dir)
    generator = list_candidates_recursively(request_executor, mycloud_dir)
    for is_partial, files in generator:
        try:
            if is_partial:
                convert_partials(request_executor, local_dir, mycloud_dir, files)
            else:
                convert_file(request_executor, local_dir, mycloud_dir, files[0])
        except TimeoutException:
            log('Timeout while accessing resources', error=True)
        except Exception as ex:
            log(str(ex), error=True)
            traceback.print_exc()


def convert_partials(request_executor: MyCloudRequestExecutor,
                     local_dir: str,
                     remote_dir: str,
                     files):
    base_directory = os.path.dirname(files[0])
    log(f'Converting partial files in {base_directory}...')



def convert_file(request_executor: MyCloudRequestExecutor,
                 local_dir: str,
                 remote_dir: str,
                 remote_file: str):
    log(f'Converting file {remote_file}...')
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    local_file = resource_builder.build_local_file(remote_file)
    log(f'Mapped {remote_file} to local file {local_file}')
    if not os.path.isfile(local_file):
        log(f'File {local_file} not found. Defaulting to version {DEFAULT_VERSION}')
        version = BasicStringVersion(DEFAULT_VERSION)
        translatable_path = BasicRemotePath(remote_file)
    else:
        log(f'Found local file {local_file}. Using hash calculated version and uploading properties...')
        version = HashCalculatedVersion(local_file)
        translatable_path = LocalTranslatablePath(resource_builder, local_file, version)

    TEMP_FILE_EXTENSION = '.temporary'
    versioned_stream_accessor = VersionedCloudStreamAccessor(translatable_path, version, None)
    partial_destination = versioned_stream_accessor.get_part_file(0)

    temporary_file = remote_file + TEMP_FILE_EXTENSION
    log(f'Renaming file {remote_file} to {partial_destination} through {temporary_file}...')
    request_executor.execute_request(RenameRequest(remote_file, temporary_file, is_file=True))
    request_executor.execute_request(RenameRequest(temporary_file, partial_destination, is_file=True))
    log(f'Renamed file successfully')

    _create_file_metadata(request_executor,
                          version,
                          translatable_path,
                          remote_file,
                          [partial_destination],
                          resource_builder)


def list_candidates_recursively(request_executor: MyCloudRequestExecutor, mycloud_dir: str):
    req = MetadataRequest(mycloud_dir, ignore_not_found=True)
    response = request_executor.execute_request(req)
    (dirs, files) = MetadataRequest.format_response(response)
    if len(files) == 1 and files[0]['Name'] == METADATA_FILE_NAME:
        metadata_path = files[0]['Path']
        log(f'Skipping {metadata_path} and subdirectories, because it was already converted...')
        return
        yield

    partial_directory = _is_partial_directory(files)

    if partial_directory:
        yield True, [file['Path'] for file in files]
    else:
        for file in files:
            yield False, [file['Path']]

    for dir in dirs:
        yield from list_candidates_recursively(request_executor, dir['Path'])


def _is_partial_directory(files):
    if not all([PARTIAL_EXTENSION in file['Path'] for file in files]) or len(files) == 0:
        return False

    for file in files:
        number = file['Name'][:START_NUMBER_LENGTH]
        if not is_int(number):
            return False

    return True


def _create_file_metadata(request_executor: MyCloudRequestExecutor,
                          version: CalculatableVersion,
                          translatable_path: TranslatablePath,
                          remote_file: str,
                          partial_files,
                          resource_builder: ObjectResourceBuilder):
    file_version = Version(version.calculate_version(), remote_file)
    for partial_file in partial_files:
        file_version.add_part_file(partial_file)
    if resource_builder.ends_with_aes_extension(remote_file):
        transform = AES256CryptoTransform(AES_EXTENSION)
        file_version.add_transform(transform.get_name())
    properties = translatable_path.calculate_properties()
    for key in properties:
        file_version.add_property(key, properties[key])
    metadata = FileMetadata()
    metadata.update_version(file_version)

    log(f'Uploading vesion {file_version.get_identifier()}...')
    manager = MetadataManager(request_executor)
    manager.update_metadata(translatable_path, metadata)
    log(f'Successfully converted file {remote_file}')