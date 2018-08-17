import os
from random import shuffle
from mycloud.logger import log
from mycloud.mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from mycloud.filesystem import FileManager, LocalTranslatablePath, HashCalculatedVersion
from mycloud.streamapi.transforms import AES256CryptoTransform
from mycloud.streamapi import DefaultUpStream, ProgressReporter
from mycloud.constants import MY_CLOUD_BIG_FILE_CHUNK_SIZE
from mycloud.helper import operation_timeout, TimeoutException
from mycloud.filesync.progress import ProgressTracker


def upsync_folder(request_executor: MyCloudRequestExecutor,
                  resource_builder: ObjectResourceBuilder,
                  local_directory: str,
                  progress_tracker: ProgressTracker,
                  encryption_pwd: str = None):
    for root, dirs, files in os.walk(local_directory, topdown=True):
        shuffle(dirs)
        for file in files:
            local_file = os.path.join(root, file)
            try:
                upsync_file(request_executor, resource_builder,
                            local_file, progress_tracker, encryption_pwd)
            except TimeoutException:
                log('Failed to access file {} within the given time'.format(local_file), error=True)
            except ValueError as ex:
                log(str(ex), error=True)
            except Exception as ex:
                log('Unhandled exception: {}'.format(str(ex)), error=True)


def upsync_file(request_executor: MyCloudRequestExecutor,
                resource_builder: ObjectResourceBuilder,
                local_file: str,
                progress_tracker: ProgressTracker,
                encryption_pwd: str = None):
    if progress_tracker.skip_file(local_file):
        log('Skipping file {}'.format(local_file))
        return

    transforms = [] if encryption_pwd is None else [
        AES256CryptoTransform(encryption_pwd)]
    del encryption_pwd
    file_manager = FileManager(
        request_executor, transforms, ProgressReporter())
    remote_path = resource_builder.build_remote_file(local_file)
    calculatable_version = HashCalculatedVersion(local_file)
    translatable_path = LocalTranslatablePath(
        resource_builder, local_file, calculatable_version)
    started_partial_upload, index = file_manager.started_partial_upload(
        translatable_path, calculatable_version)
    local_stream = operation_timeout(
        lambda x: open(x['path'], 'rb'), path=local_file)
    if started_partial_upload:
        stream_position = index * MY_CLOUD_BIG_FILE_CHUNK_SIZE
        operation_timeout(lambda x: x['stream'].seek(
            x['pos']), stream=local_stream, pos=stream_position)
    cloud_stream = DefaultUpStream(local_stream, index)
    file_manager.write_file(
        cloud_stream, translatable_path, calculatable_version)
