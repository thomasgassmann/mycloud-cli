import os
import traceback
from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder
from mycloud.filesystem import TranslatablePath, FileManager, BasicStringVersion
from mycloud.streamapi import ProgressReporter, DefaultDownStream
from mycloud.streamapi.transforms import AES256CryptoTransform
from mycloud.logger import log
from mycloud.helper import TimeoutException, operation_timeout
from mycloud.constants import MY_CLOUD_BIG_FILE_CHUNK_SIZE


def downsync_folder(request_executor: MyCloudRequestExecutor,
                    resource_builder: ObjectResourceBuilder,
                    remote_directory: TranslatablePath,
                    progress_tracker: ProgressTracker,
                    decryption_pwd: str = None):
    # No transforms needed just to read directory
    file_manager = FileManager(request_executor, [], ProgressReporter())
    generator = file_manager.read_directory(remote_directory, recursive=True)
    for file in generator:
        try:
            downsync_file(request_executor, resource_builder,
                          file, progress_tracker, decryption_pwd)
        except TimeoutException:
            log(f'Failed to write to the local file within the given time', error=True)
        except ValueError as ex:
            log(f'{str(ex)}', error=True)
        except Exception as ex:
            log(f'Unhandled exception: {str(ex)}', error=True)
            traceback.print_exc()


def downsync_file(request_executor: MyCloudRequestExecutor,
                  resource_builder: ObjectResourceBuilder,
                  remote_file: TranslatablePath,
                  progress_tracker: ProgressTracker,
                  decryption_pwd: str = None):
    if progress_tracker.skip_file(remote_file.calculate_remote()):
        return

    transforms = [] if decryption_pwd is None else [AES256CryptoTransform(
        decryption_pwd)]
    del decryption_pwd
    file_manager = FileManager(
        request_executor, transforms, ProgressReporter())

    remote_base_path = remote_file.calculate_remote()
    metadata = file_manager.read_file_metadata(remote_file)
    latest_version = metadata.get_latest_version()
    basic_version = BasicStringVersion(latest_version.get_identifier())
    local_file = resource_builder.build_local_file(remote_base_path)
    skip, started_partial, partial_index = file_manager.started_partial_download(remote_file,
                                                                                 basic_version,
                                                                                 local_file)
    if skip:
        return

    local_stream = operation_timeout(lambda x: open(
        x['local_file'], 'ab'), local_file=local_file)
    if started_partial:
        operation_timeout(lambda x: x['stream'].seek(
            x['len']), stream=local_stream, len=partial_index * MY_CLOUD_BIG_FILE_CHUNK_SIZE)

    downstream = DefaultDownStream(local_stream, partial_index)
    file_manager.read_file(downstream, remote_file, basic_version)
