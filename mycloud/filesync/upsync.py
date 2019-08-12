import os
import logging
from mycloud.mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from mycloud.filesystem import FileManager, LocalTranslatablePath, HashCalculatedVersion
from mycloud.streamapi.transforms import AES256CryptoTransform
from mycloud.streamapi import DefaultUpStream, ProgressReporter
from mycloud.constants import MY_CLOUD_BIG_FILE_CHUNK_SIZE
from mycloud.common import operation_timeout, TimeoutException
from mycloud.filesync.progress import ProgressTracker


# _mtime_cache = {}


async def upsync_folder(request_executor: MyCloudRequestExecutor,
                  resource_builder: ObjectResourceBuilder,
                  local_directory: str,
                  progress_tracker: ProgressTracker,
                  encryption_pwd: str = None,
                  skip_by_date=True):
    # global _mtime_cache
    # skip_by_date: Use ctime of mycloud_metadata.json
    for root, _, files in os.walk(local_directory, topdown=True):
        # remote_root = resource_builder._build_remote_directory(root)
        # if not _cache_contains(remote_root):
        #     _fill_mtime(request_executor, remote_root)
        for file in files:
            local_file = os.path.join(root, file)
            try:
                await upsync_file(request_executor, resource_builder,
                            local_file, progress_tracker, encryption_pwd, skip_by_date)
            except TimeoutException:
                logging.error('Failed to access file {} within the given time'.format(
                    local_file))
            except ValueError as ex:
                logging.error(str(ex))


async def upsync_file(request_executor: MyCloudRequestExecutor,
                resource_builder: ObjectResourceBuilder,
                local_file: str,
                progress_tracker: ProgressTracker,
                encryption_pwd: str = None,
                skip_by_date=True):
    # global _mtime_cache
    if progress_tracker.skip_file(local_file):
        logging.info('Skipping file {}'.format(local_file))
        return

    # remote_path = resource_builder.build_remote_file(local_file)
    # local_mtime = operation_timeout(
    #     lambda x: os.path.getmtime(x['path']), path=local_file)
    # if skip_by_date and _mtime_cache[remote_path] >= local_mtime:
    #     log('Skipping file becuase of mtime {}'.format(remote_path))
    #     return

    transforms = [] if encryption_pwd is None else [
        AES256CryptoTransform(encryption_pwd)]
    del encryption_pwd
    file_manager = FileManager(
        request_executor, transforms, ProgressReporter())
    calculatable_version = HashCalculatedVersion(local_file)
    translatable_path = LocalTranslatablePath(
        resource_builder, local_file, calculatable_version)
    started_partial_upload, index = await file_manager.started_partial_upload(
        translatable_path, calculatable_version)
    local_stream = operation_timeout(
        lambda x: open(x['path'], 'rb'), path=local_file)
    if started_partial_upload:
        stream_position = index * MY_CLOUD_BIG_FILE_CHUNK_SIZE
        operation_timeout(lambda x: x['stream'].seek(
            x['pos']), stream=local_stream, pos=stream_position)
    cloud_stream = DefaultUpStream(local_stream, index)
    await file_manager.write_file(
        cloud_stream, translatable_path, calculatable_version)


# def _fill_mtime(request_executor: MyCloudRequestExecutor, directory: str):
#     # global _mtime_cache
#     directory_list_request = DirectoryListRequest(directory,
#                                                   ListType.File,
#                                                   ignore_not_found=True,
#                                                   ignore_internal_server_error=True)
#     response = request_executor.execute_request(directory_list_request)
#     if response.status_code == 404:
#         return

#     is_timeout = DirectoryListRequest.is_timeout(response)
#     if is_timeout:
#         return

#     files = directory_list_request.format_response(response)
#     for file in files:
#         file_path = file['Path']
#         if os.path.basename(file_path) == METADATA_FILE_NAME:
#             ticks = file['ModificationTimeTicks']
#             unix_time = to_unix_timestamp(ticks)
#             dir_path = os.path.dirname(file_path)
#             _mtime_cache[dir_path] = unix_time


# def _cache_contains(dir: str):
#     global _mtime_cache
#     for key in _mtime_cache:
#         if dir in key:
#             return True
#     return False


# def _clear_mtime_cache(current_path: str):
#     pass
