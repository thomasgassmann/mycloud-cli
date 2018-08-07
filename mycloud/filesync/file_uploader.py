import os
from random import shuffle
from mycloud.constants import SAVE_FREQUENCY, MY_CLOUD_BIG_FILE_CHUNK_SIZE
from mycloud.logger import log
from mycloud.mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor, MetadataRequest
from mycloud.filesync.versioned_stream_accessor import VersionedCloudStreamAccessor
from mycloud.streamapi import DefaultUpStream, UpStreamExecutor, ProgressReporter
from mycloud.streamapi.transforms import AES256EncryptTransform
from mycloud.filesync.progress import ProgressTracker
from mycloud.helper import operation_timeout, TimeoutException


def _get_file_stream(file_path: str):
    def open_file(vals):
        return open(vals['path'], 'rb')
    stream = operation_timeout(open_file, path=file_path)
    return stream


def _get_file_length(file_path: str):
    def os_stat(vals):
        return os.stat(vals['path'])
    stats = operation_timeout(os_stat, path=file_path)
    return stats.st_size


def upload(request_executor: MyCloudRequestExecutor,
           local_directory: str,
           tracker: ProgressTracker,
           encryption_password: str,
           builder: ObjectResourceBuilder):
    current_iteration = 0
    upstreamer = UpStreamExecutor(request_executor, ProgressReporter())
    for root, dirs, files in os.walk(local_directory, topdown=True):
        shuffle(dirs)
        for file in files:
            local = os.path.join(root, file)
            remote = builder.build_remote_file(local)
            try:
                upload_file(upstreamer, local, remote,
                            encryption_password, tracker)
            except TimeoutException as ex:
                # TODO: retry?
                log('Timeout?')
            except Exception as ex:
                # TODO: handle
                log(str(ex), error=True)
            if current_iteration % SAVE_FREQUENCY == 0:
                tracker.try_save()
            current_iteration += 1


def upload_file(upstreamer: UpStreamExecutor,
                local_path: str,
                remote_base_path: str,
                password: str,
                tracker: ProgressTracker):
    if tracker.skip_file(remote_base_path):
        log(f'Skipping file {local_path}')
        return

    stream = _get_file_stream(local_path)
    cloud_stream = DefaultUpStream(stream)

    stream_accessor = VersionedCloudStreamAccessor(
        local_path, remote_base_path, cloud_stream)
    if password is not None:
        stream_accessor.add_transform(AES256EncryptTransform(password))

    version = stream_accessor.get_version()
    processed_parts = tracker.file_handled(
        local_path, remote_base_path, version)
    continued_append_at_part_index = len(processed_parts)
    continued_append_at_part_index = continued_append_at_part_index if continued_append_at_part_index > 0 else 0

    expected_stream_position = MY_CLOUD_BIG_FILE_CHUNK_SIZE * \
        continued_append_at_part_index
    actual_file_length = _get_file_length(local_path)
    if actual_file_length < expected_stream_position:
        log(f'Already uploaded {local_path} in version {version}')
        return

    if continued_append_at_part_index > 0:
        cloud_stream.continued_append_starting_at_part_index = continued_append_at_part_index
        log(
            f'Continueing to upload file at part {continued_append_at_part_index}')
        stream.seek(continued_append_at_part_index *
                    MY_CLOUD_BIG_FILE_CHUNK_SIZE)
        for path in processed_parts:
            stream_accessor._current_version_file_parts.append(path)

    # metadata_request = MetadataRequest(stream_accessor.get_base_path(), ignore_not_found=True)
    # response = upstreamer.request_executor.execute_request(metadata_request)
    # if response.status_code != 404:
    #     return
    # TODO: handle overwrite if version with same hash already exists
    # TODO: implement continued_append_starting_at_part_index
    # TODO: continued append may loose state in versionedstreamaccessor for parts array
    # Solve using progress tracker correctly
    log('Uploading stream...')
    upstreamer.upload_stream(stream_accessor)
    version = stream_accessor.get_version()
    tracker.track_progress(local_path, remote_base_path, version)
