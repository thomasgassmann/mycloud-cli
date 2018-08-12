import os
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

def convert_partials(request_executor: MyCloudRequestExecutor,
                     local_dir: str,
                     remote_dir: str,
                     files):
    base_directory = os.path.dirname(files[0])
    log(f'Converting partial files in {base_directory}...')
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    local_file = resource_builder.build_local_file(base_directory, remove_extension=False)
    log(f'Mapped partial files in directory {base_directory} to local file {local_file}')

    translatable_path, version = _get_path_and_version_for_local_file(local_file, base_directory, resource_builder)

    versioned_stream_accessor = VersionedCloudStreamAccessor(translatable_path, version, None)
    sorted_files = sorted(files)
    parts = []
    for sorted_file in sorted_files:
        file_name = os.path.basename(sorted_file)
        if is_int(file_name[:START_NUMBER_LENGTH]):
            index = int(file_name[:START_NUMBER_LENGTH])
            partial_file = versioned_stream_accessor.get_part_file(index)
            parts.append(partial_file)

            rename_request = RenameRequest(sorted_file, partial_file, is_file=True)
            _ = request_executor.execute_request(rename_request)

        else:
            raise ValueError('Part index could not be found in partial file')

    _create_file_metadata(request_executor,
                          version,
                          translatable_path,
                          base_directory,
                          parts,
                          resource_builder,
                          all([AES_EXTENSION in sorted_file for sorted_file in sorted_files]))


def convert_file(request_executor: MyCloudRequestExecutor,
                 local_dir: str,
                 remote_dir: str,
                 remote_file: str):
    log(f'Converting file {remote_file}...')
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    local_file = resource_builder.build_local_file(remote_file)
    log(f'Mapped {remote_file} to local file {local_file}')

    remote_file_without_aes_extension = remote_file
    if resource_builder.ends_with_aes_extension(remote_file):
        remote_file_without_aes_extension = remote_file[:-len(AES_EXTENSION)]

    translatable_path, version = _get_path_and_version_for_local_file(local_file,
                                                                    remote_file_without_aes_extension,
                                                                    resource_builder)

    TEMP_FILE_EXTENSION = '.temporary'
    versioned_stream_accessor = VersionedCloudStreamAccessor(translatable_path, version, None)
    partial_destination = versioned_stream_accessor.get_part_file(0)

    temporary_file = remote_file + TEMP_FILE_EXTENSION
    log(f'Renaming filxe {remote_file} to {partial_destination}...')
    while True:
        rename_request = RenameRequest(remote_file, temporary_file, is_file=True, ignore_conflict=True)
        response = request_executor.execute_request(rename_request)
        if response.status_code == 409:
            temporary_file += TEMP_FILE_EXTENSION
        else:
            break
    rename_request = RenameRequest(temporary_file, partial_destination, is_file=True, ignore_conflict=True)
    response = request_executor.execute_request(rename_request)
    if response.status_code == 409:
        log(f'', error=True)
        # TODO: delete file?
        return

    log(f'Renamed file successfully')

    _create_file_metadata(request_executor,
                          version,
                          translatable_path,
                          remote_file_without_aes_extension,
                          [partial_destination],
                          resource_builder,
                          resource_builder.ends_with_aes_extension(remote_file))


def list_candidates_recursively(request_executor: MyCloudRequestExecutor, mycloud_dir: str):
    req = MetadataRequest(mycloud_dir, ignore_not_found=True)
    try:
        response = request_executor.execute_request(req)
    except TimeoutException:
        return

    (dirs, files) = MetadataRequest.format_response(response)
    if len(files) == 1 and files[0]['Name'] == METADATA_FILE_NAME and len(dirs) != 0:
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


def _get_path_and_version_for_local_file(local_file: str, remote_file: str, resource_builder: ObjectResourceBuilder):
    if not os.path.isfile(local_file):
        log(f'File {local_file} not found. Defaulting to version {DEFAULT_VERSION}')
        version = BasicStringVersion(DEFAULT_VERSION)
        translatable_path = BasicRemotePath(remote_file)
    else:
        log(f'Found local file {local_file}. Using hash calculated version and uploading properties...')
        version = HashCalculatedVersion(local_file)
        translatable_path = LocalTranslatablePath(resource_builder, local_file, version)
    return translatable_path, version


def _create_file_metadata(request_executor: MyCloudRequestExecutor,
                          version: CalculatableVersion,
                          translatable_path: TranslatablePath,
                          remote_file: str,
                          partial_files,
                          resource_builder: ObjectResourceBuilder,
                          is_encrypted: bool):
    file_version = Version(version.calculate_version(), remote_file)
    for partial_file in partial_files:
        file_version.add_part_file(partial_file)
    if is_encrypted:
        transform = AES256CryptoTransform(AES_EXTENSION)
        file_version.add_transform(transform.get_name())
    properties = translatable_path.calculate_properties()
    for key in properties:
        file_version.add_property(key, properties[key])
    metadata = FileMetadata()
    metadata.update_version(file_version)

    log(f'Uploading version {file_version.get_identifier()}...')
    manager = MetadataManager(request_executor)
    manager.update_metadata(translatable_path, metadata)
    log(f'Successfully converted file {remote_file}')