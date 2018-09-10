import os
import sys
import gc
from collections import defaultdict
from typing import List
from threading import Thread
from mycloud.helper import operation_timeout
from mycloud.mycloudapi import (
    MyCloudRequestExecutor,
    ObjectResourceBuilder,
    RenameRequest,
    MetadataRequest,
    DirectoryListRequest,
    ListType
)
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
    METADATA_FILE_NAME,
    MAX_THREADS_FOR_REMOTE_FILE_CONVERSION
)
from mycloud.filesync.tree import RelativeFileTree
from mycloud.filesystem.versioned_stream_accessor import VersionedCloudStreamAccessor
from mycloud.streamapi import ProgressReporter
from mycloud.streamapi.transforms import AES256CryptoTransform
from mycloud.helper import get_all_files_recursively, is_int, TimeoutException
from mycloud.logger import log


def convert_remote_files(request_executor: MyCloudRequestExecutor,
                         mycloud_dir: str,
                         local_dir: str,
                         skip):
    resource_builder = ObjectResourceBuilder(local_dir, mycloud_dir)

    def _skip(file):
        for item in skip:
            if file.startswith(item):
                return True
        return False
    threads = []
    thread_file_sizes = {}

    def del_thread(thread):
        log('Deleting thread {}'.format(thread.ident))
        if thread in threads:
            # TODO: kill thread
            threads.remove(thread)
        else:
            log('Thread {} not found in thread list'.format(
                thread.ident), error=True)
        if thread.ident in thread_file_sizes:
            del thread_file_sizes[thread.ident]
        else:
            log('Thread file size for thread {} not found in dictionary'.format(
                thread.ident), error=True)

    generator = list_candidates_recursively(request_executor, mycloud_dir)

    for is_partial, files in generator:
        try:
            thread = Thread(target=convert, args=(
                is_partial, files, request_executor, local_dir, mycloud_dir, _skip))
            thread.daemon = True
            local_file = get_local_file(
                is_partial, files, mycloud_dir, local_dir)
            file_size = operation_timeout(
                lambda x: os.stat(x['path']).st_size if os.path.isfile(x['path']) else 0, path=local_file)
            thread.start()
            thread_file_sizes[thread.ident] = file_size
            threads.append(thread)
        except TimeoutException:
            log('Timeout while accessing resources', error=True)
        except Exception as ex:
            log(str(ex), error=True)

        to_be_removed = [thread for thread in threads if not thread.is_alive()]
        for thread_to_be_removed in to_be_removed:
            del_thread(thread_to_be_removed)

        if len(threads) >= MAX_THREADS_FOR_REMOTE_FILE_CONVERSION:
            log('More than 10 threads active... Searching for a thread to join...')
            min_file_size_thread = min(
                thread_file_sizes, key=thread_file_sizes.get)
            log('Found thread with least amount of work to join (id {})'.format(
                min_file_size_thread))
            thread = list(filter(lambda t: t.ident ==
                                 min_file_size_thread, threads))[0]
            log('Got thread {} from list... Joining thread...'.format(thread.ident))
            thread.join()
            log('Finished joining thread... Removing thread from list {}'.format(
                thread.ident))
            del_thread(thread)


def convert(is_partial, files, request_executor, local_dir, mycloud_dir, _skip):
    if is_partial:
        convert_partials(request_executor, local_dir,
                         mycloud_dir, files, _skip)
    else:
        convert_file(request_executor, local_dir,
                     mycloud_dir, files[0], _skip)


def get_local_file(is_partial: bool, files: List[str], remote_dir: str, local_dir: str):
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    if not is_partial:
        return resource_builder.build_local_file(files[0])
    else:
        base_directories = [os.path.dirname(file) for file in files]
        distinct_base_directories = set(base_directories)
        if len(distinct_base_directories) != 1:
            raise ValueError('A file cannot have multiple base directories')
        base_directory = base_directories[0]
        return resource_builder.build_local_file(base_directory, remove_extension=False)


def convert_partials(request_executor: MyCloudRequestExecutor,
                     local_dir: str,
                     remote_dir: str,
                     files,
                     skip_fn):
    base_directory = os.path.dirname(files[0])
    log('Converting partial files in {}...'.format(base_directory))
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    local_file = get_local_file(True, files, remote_dir, local_dir)
    log('Mapped partial files in directory {} to local file {}'.format(
        base_directory, local_file))

    translatable_path, version = _get_path_and_version_for_local_file(local_file,
                                                                      base_directory,
                                                                      resource_builder,
                                                                      skip_fn(local_file))

    versioned_stream_accessor = VersionedCloudStreamAccessor(
        translatable_path, version, None)
    sorted_files = sorted(files)
    parts = []
    for sorted_file in sorted_files:
        file_name = os.path.basename(sorted_file)
        if is_int(file_name[:START_NUMBER_LENGTH]):
            index = int(file_name[:START_NUMBER_LENGTH])
            partial_file = versioned_stream_accessor.get_part_file(index)
            parts.append(partial_file)

            rename_request = RenameRequest(
                sorted_file, partial_file, is_file=True)
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
                 remote_file: str,
                 skip_fn):
    log('Converting file {}...'.format(remote_file))
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    local_file = get_local_file(False, [remote_file], remote_dir, local_dir)
    log('Mapped {} to local file {}'.format(remote_file, local_file))

    remote_file_without_aes_extension = remote_file
    if resource_builder.ends_with_aes_extension(remote_file):
        remote_file_without_aes_extension = remote_file[:-len(AES_EXTENSION)]

    translatable_path, version = _get_path_and_version_for_local_file(local_file,
                                                                      remote_file_without_aes_extension,
                                                                      resource_builder,
                                                                      skip_fn(local_file))

    TEMP_FILE_EXTENSION = '.temporary'
    versioned_stream_accessor = VersionedCloudStreamAccessor(
        translatable_path, version, None)
    partial_destination = versioned_stream_accessor.get_part_file(0)

    temporary_file = remote_file + TEMP_FILE_EXTENSION
    log('Renaming file {} to {}...'.format(remote_file, partial_destination))
    while True:
        rename_request = RenameRequest(
            remote_file, temporary_file, is_file=True, ignore_conflict=True)
        response = request_executor.execute_request(rename_request)
        if response.status_code == 409:
            temporary_file += TEMP_FILE_EXTENSION
        else:
            break
    rename_request = RenameRequest(
        temporary_file, partial_destination, is_file=True, ignore_conflict=True)
    response = request_executor.execute_request(rename_request)
    if response.status_code == 409:
        log(f'File already exists at {partial_destination}!', error=True)
        return

    log('Renamed file successfully')

    _create_file_metadata(request_executor,
                          version,
                          translatable_path,
                          remote_file_without_aes_extension,
                          [partial_destination],
                          resource_builder,
                          resource_builder.ends_with_aes_extension(remote_file))


def list_candidates_recursively(request_executor: MyCloudRequestExecutor, mycloud_dir: str):
    log(f'Listing directory {mycloud_dir}...')
    log(f'Trying to read entire directory {mycloud_dir} at once...')
    list_request = DirectoryListRequest(mycloud_dir, ListType.File,
                                        ignore_internal_server_error=True, ignore_not_found=True)
    failed = False
    try:
        list_response = request_executor.execute_request(list_request)
    except requests.exceptions.ConnectionError:
        log(
            f'Failed to execute directory list on dir {mycloud_dir}... Continueing with usual directory list')
        failed = True
    if list_response.status_code == 404:
        log(f'Directory {mycloud_dir} not found... Returning')
        return
    elif not failed and not DirectoryListRequest.is_timeout(list_response):
        log(
            f'Server returned successful response for entire directory {mycloud_dir}')
        files = DirectoryListRequest.format_response(list_response)
        tree = RelativeFileTree()
        for file in files:
            tree.add_file(file['Path'], mycloud_dir)

        log(f'Added {tree.file_count} files to the relative file tree...')
        del files
        yield from tree.loop()

        del tree
        gc.collect()

        return

    log(
        f'Couldn\'t list entire directory at once... Listing directory {mycloud_dir} in a flat way')
    metadata_request = MetadataRequest(mycloud_dir, ignore_not_found=True)
    metadata_response = None
    try:
        metadata_response = request_executor.execute_request(metadata_request)
    except TimeoutException:
        log(
            f'Timeout when trying to list directory {mycloud_dir}. Returning', error=True)
        return
    except Exception as ex:
        log('Failed to list directory: {}'.format(str(ex)))
        log('Retrying to list directory {}...'.format(mycloud_dir))
        yield from list_candidates_recursively(request_executor, mycloud_dir)
        return

    (dirs, files) = MetadataRequest.format_response(metadata_response)
    dirs = [dir['Path'] for dir in dirs]
    files = [file['Path'] for file in files]

    generator = RelativeFileTree.get_directory_generator(files, dirs)
    continue_traversal = next(generator)
    if not continue_traversal:
        return

    yield from generator

    for dir in dirs:
        yield from list_candidates_recursively(request_executor, dir)


def _get_path_and_version_for_local_file(local_file: str, remote_file: str, resource_builder: ObjectResourceBuilder, no_hash: bool = False):
    if not os.path.isfile(local_file) or no_hash:
        log('File {} not found. Defaulting to version {}'.format(
            local_file, DEFAULT_VERSION))
        version = BasicStringVersion(DEFAULT_VERSION)
        translatable_path = BasicRemotePath(remote_file)
    else:
        log('Found local file {}. Using hash calculated version and uploading properties...'.format(local_file))
        version = HashCalculatedVersion(local_file)
        translatable_path = LocalTranslatablePath(
            resource_builder, local_file, version)
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

    log('Uploading version {}...'.format(file_version.get_identifier()))
    manager = MetadataManager(request_executor)
    manager.update_metadata(translatable_path, metadata)
    log('Successfully converted file {}'.format(remote_file))
