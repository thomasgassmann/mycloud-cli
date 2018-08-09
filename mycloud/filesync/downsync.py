import os
import tempfile
from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder
from mycloud.filesystem import TranslatablePath, FileManager, BasicStringVersion
from mycloud.streamapi import ProgressReporter, DefaultDownStream
from mycloud.streamapi.transforms import AES256CryptoTransform
from mycloud.logger import log
from mycloud.helper import TimeoutException, operation_timeout
from mycloud.constants import MY_CLOUD_BIG_FILE_CHUNK_SIZE, ENCRYPTION_CHUNK_LENGTH


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

    # Can't use append
    # https://stackoverflow.com/questions/29013495/opening-file-in-append-mode-and-seeking-to-start
    if started_partial:
        # Delete file content after partial_index * MY_CLOUD_BIG_FILE_CHUNK_SIZE -> then append
        delete_bytes_after = partial_index * MY_CLOUD_BIG_FILE_CHUNK_SIZE
        file_length = operation_timeout(lambda x: os.stat(
            x['local_file']).st_size, local_file=local_file)
        if file_length != delete_bytes_after:
            fd, temp_path = tempfile.mkstemp()
            if MY_CLOUD_BIG_FILE_CHUNK_SIZE % ENCRYPTION_CHUNK_LENGTH != 0:
                raise ValueError(
                    'Chunk size in myCloud must be a multiple of encryption chunk length')

            read_stream = operation_timeout(lambda x: open(
                x['local_file'], 'rb'), local_file=local_file)
            with os.fdopen(fd, 'wb') as f:
                read_length = 0
                while read_length != delete_bytes_after:
                    read_values = read_stream.read(ENCRYPTION_CHUNK_LENGTH)
                    f.write(read_values)
                    read_length += ENCRYPTION_CHUNK_LENGTH
            read_stream.close()
            os.remove(local_file)

            os.rename(temp_path, local_file)

        local_stream = operation_timeout(lambda x: open(
            x['local_file'], 'ab'), local_file=local_file)
    else:
        local_stream = operation_timeout(lambda x: open(
            x['local_file'], 'wb'), local_file=local_file)

    downstream = DefaultDownStream(local_stream, partial_index)
    file_manager.read_file(downstream, remote_file, basic_version)
    local_stream.close()
