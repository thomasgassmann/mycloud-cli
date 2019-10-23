import os
import gc
import logging
from typing import List
from threading import Thread
import requests
from mycloud.common import operation_timeout
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder
from mycloud.mycloudapi.requests.drive import RenameRequest, MetadataRequest, DirectoryListRequest, ListType
from mycloud.filesystem import (
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
    START_NUMBER_LENGTH,
    DEFAULT_VERSION,
    AES_EXTENSION,
    MAX_THREADS_FOR_REMOTE_FILE_CONVERSION
)
from mycloud.filesync.tree import RelativeFileTree
from mycloud.filesystem.versioned_stream_accessor import VersionedCloudStreamAccessor
from mycloud.streamapi.transforms import AES256CryptoTransform
from mycloud.common import is_int, TimeoutException


async def convert_remote_files(request_executor: MyCloudRequestExecutor,
                         mycloud_dir: str,
                         local_dir: str,
                         skip):
    def _skip(file):
        for item in skip:
            if file.startswith(item):
                return True
        return False
    threads = []
    thread_file_sizes = {}

    def del_thread(thread):
        logging.debug('Deleting thread {}'.format(thread.ident))
        if thread in threads:
            threads.remove(thread)
        else:
            logging.debug('Thread {} not found in thread list'.format(
                thread.ident))
        if thread.ident in thread_file_sizes:
            del thread_file_sizes[thread.ident]
        else:
            logging.debug('Thread file size for thread {} not found in dictionary'.format(
                thread.ident))

    generator = await list_candidates(request_executor, mycloud_dir)

    def get_file_size(file_obj):
        return os.stat(file_obj['path']).st_size if os.path.isfile(file_obj['path']) else 0
    for is_partial, files in generator:
        try:
            thread = Thread(target=convert, args=(
                is_partial, files, request_executor, local_dir, mycloud_dir, _skip))
            thread.daemon = True
            local_file = get_local_file(
                is_partial, files, mycloud_dir, local_dir)
            file_size = operation_timeout(
                get_file_size, path=local_file)
            thread.start()
            thread_file_sizes[thread.ident] = file_size
            threads.append(thread)
        except TimeoutException:
            logging.error('Timeout while accessing resources')

        to_be_removed = [thread for thread in threads if not thread.is_alive()]
        for thread_to_be_removed in to_be_removed:
            del_thread(thread_to_be_removed)

        if len(threads) >= MAX_THREADS_FOR_REMOTE_FILE_CONVERSION:
            logging.debug(
                'More than 10 threads active... Searching for a thread to join...')
            min_file_size_thread = min(
                thread_file_sizes, key=thread_file_sizes.get)
            logging.debug('Found thread with least amount of work to join (id {})'.format(
                min_file_size_thread))
            thread = list(filter(lambda t: t.ident ==
                                 min_file_size_thread, threads))[0]
            logging.debug(
                'Got thread {} from list... Joining thread...'.format(thread.ident))
            thread.join()
            logging.debug('Finished joining thread... Removing thread from list {}'.format(
                thread.ident))
            del_thread(thread)


async def convert(is_partial, files, request_executor, local_dir, mycloud_dir, _skip):
    if is_partial:
        await convert_partials(request_executor, local_dir,
                         mycloud_dir, files, _skip)
    else:
        await convert_file(request_executor, local_dir,
                     mycloud_dir, files[0], _skip)


def get_local_file(is_partial: bool, files: List[str], remote_dir: str, local_dir: str):
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    if not is_partial:
        return resource_builder.build_local_file(files[0])

    base_directories = [os.path.dirname(file) for file in files]
    distinct_base_directories = set(base_directories)
    if len(distinct_base_directories) != 1:
        raise ValueError('A file cannot have multiple base directories')
    base_directory = base_directories[0]
    return resource_builder.build_local_file(base_directory, remove_extension=False)


async def convert_partials(request_executor: MyCloudRequestExecutor,
                     local_dir: str,
                     remote_dir: str,
                     files,
                     skip_fn):
    base_directory = os.path.dirname(files[0])
    logging.info('Converting partial files in {}...'.format(base_directory))
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    local_file = get_local_file(True, files, remote_dir, local_dir)
    logging.info('Mapped partial files in directory {} to local file {}'.format(
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
            _ = await request_executor.execute_request(rename_request)

        else:
            raise ValueError('Part index could not be found in partial file')

    await _create_file_metadata(request_executor,
                          version,
                          translatable_path,
                          base_directory,
                          parts,
                          resource_builder,
                          all([AES_EXTENSION in sorted_file for sorted_file in sorted_files]))


async def convert_file(request_executor: MyCloudRequestExecutor,
                 local_dir: str,
                 remote_dir: str,
                 remote_file: str,
                 skip_fn):
    logging.info('Converting file {}...'.format(remote_file))
    resource_builder = ObjectResourceBuilder(local_dir, remote_dir)
    local_file = get_local_file(False, [remote_file], remote_dir, local_dir)
    logging.info('Mapped {} to local file {}'.format(remote_file, local_file))

    without_aes_extension = remote_file
    if resource_builder.ends_with_aes_extension(remote_file):
        without_aes_extension = remote_file[:-len(AES_EXTENSION)]

    translatable_path, version = _get_path_and_version_for_local_file(local_file,
                                                                      without_aes_extension,
                                                                      resource_builder,
                                                                      skip_fn(local_file))

    temp_file_extension = '.temporary'
    versioned_stream_accessor = VersionedCloudStreamAccessor(
        translatable_path, version, None)
    partial_destination = versioned_stream_accessor.get_part_file(0)

    temporary_file = remote_file + temp_file_extension
    logging.info('Renaming file {} to {}...'.format(
        remote_file, partial_destination))
    while True:
        rename_request = RenameRequest(
            remote_file, temporary_file, is_file=True, ignore_conflict=True)
        response = await request_executor.execute_request(rename_request)
        if response.status_code == 409:
            temporary_file += temp_file_extension
        else:
            break
    rename_request = RenameRequest(
        temporary_file, partial_destination, is_file=True, ignore_conflict=True)
    response = await request_executor.execute_request(rename_request)
    if response.status_code == 409:
        logging.error(
            f'File already exists at {partial_destination}!')
        return

    logging.info('Renamed file successfully')

    await _create_file_metadata(request_executor,
                          version,
                          translatable_path,
                          without_aes_extension,
                          [partial_destination],
                          resource_builder,
                          resource_builder.ends_with_aes_extension(remote_file))


async def list_candidates(request_executor: MyCloudRequestExecutor, mycloud_dir: str):
    logging.info(f'Listing directory {mycloud_dir}...')
    logging.info(f'Trying to read entire directory {mycloud_dir} at once...')
    list_request = DirectoryListRequest(mycloud_dir, ListType.File,
                                        ignore_internal_server_error=True, ignore_not_found=True)
    failed = False
    list_response = None
    try:
        list_response = await request_executor.execute_request(list_request)
    except requests.exceptions.ConnectionError:
        logging.warning(
            f'Failed to execute directory list on dir {mycloud_dir}... Continuing with usual directory list')
        failed = True

    if list_response and list_response.status_code == 404:
        logging.info(f'Directory {mycloud_dir} not found... Returning')
    elif not failed and list_response and not DirectoryListRequest.is_timeout(list_response):
        logging.info(
            f'Server returned successful response for entire directory {mycloud_dir}')
        files = list_request.format_response(list_response)
        tree = RelativeFileTree()
        for file in files:
            tree.add_file(file['Path'], mycloud_dir)

        logging.info(
            f'Added {tree.file_count} files to the relative file tree...')
        del files
        for item in tree.loop():
            yield item

        del tree
        gc.collect()
    else:
        logging.info(
            f'Couldn\'t list entire directory at once... Listing directory {mycloud_dir} in a flat way')
        metadata_request = MetadataRequest(mycloud_dir, ignore_not_found=True)
        metadata_response = None
        try:
            metadata_response = await request_executor.execute_request(
                metadata_request)
        except TimeoutException:
            logging.error(
                f'Timeout when trying to list directory {mycloud_dir}. Returning...')
            return
        except Exception as ex:
            logging.error('Failed to list directory: {}'.format(str(ex)))
            logging.error(
                'Retrying to list directory {}...'.format(mycloud_dir))
            for item in await list_candidates(request_executor, mycloud_dir):
                yield item
            return

        (dirs, files) = MetadataRequest.format_response(metadata_response)
        dirs = [dir['Path'] for dir in dirs]
        files = [file['Path'] for file in files]

        generator = RelativeFileTree.get_directory_generator(files, dirs)
        continue_traversal = next(generator)
        if not continue_traversal:
            return

        for item in generator:
            yield item

        for directory in dirs:
            for item in await list_candidates(request_executor, directory):
                yield item


def _get_path_and_version_for_local_file(local_file: str, remote_file: str, resource_builder: ObjectResourceBuilder, no_hash: bool = False):
    if not os.path.isfile(local_file) or no_hash:
        logging.warning('File {} not found. Defaulting to version {}'.format(
            local_file, DEFAULT_VERSION))
        version = BasicStringVersion(DEFAULT_VERSION)
        translatable_path = BasicRemotePath(remote_file)
    else:
        logging.info(
            'Found local file {}. Using hash calculated version and uploading properties...'.format(local_file))
        version = HashCalculatedVersion(local_file)
        translatable_path = LocalTranslatablePath(
            resource_builder, local_file, version)
    return translatable_path, version


async def _create_file_metadata(request_executor: MyCloudRequestExecutor,
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

    logging.info('Uploading version {}...'.format(
        file_version.get_identifier()))
    manager = MetadataManager(request_executor)
    await manager.update_metadata(translatable_path, metadata)
    logging.info('Successfully converted file {}'.format(remote_file))
