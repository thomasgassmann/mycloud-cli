import os
import io
import time
import threading
import signal
import sys
from io import BytesIO
from sys import platform
from threading import Thread
from filesync.progress import ProgressTracker
from helper import operation_timeout, TimeoutException
from constants import ENCRYPTION_CHUNK_LENGTH, RETRY_COUNT, SAVE_FREQUENCY, MY_CLOUD_BIG_FILE_CHUNK_SIZE
from logger import log
from collections import deque
from random import shuffle
from mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor, MetadataRequest
from filesync.versioned_stream_accessor import VersionedCloudStreamAccessor
from streamapi import DefaultUpStream, UpStreamExecutor, ProgressReporter
from streamapi.transforms import AES256EncryptTransform


def get_file_stream(file_path):
    def open_file(vals):
        return open(vals['path'], 'rb')
    stream = operation_timeout(open_file, path=file_path)
    return stream


def seek_stream(stream, part):
    def seek_file(vals):
        vals['stream'].seek(vals['sought_length'])
    operation_timeout(seek_file, stream=stream,
                      sought_length=MY_CLOUD_BIG_FILE_CHUNK_SIZE * part)


def upload(request_executor: MyCloudRequestExecutor,
           local_directory: str,
           mycloud_directory: str,
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
            except TimeoutException:
                pass
            if current_iteration % SAVE_FREQUENCY == 0:
                tracker.try_save()
            current_iteration += 1


def upload_file(upstreamer: UpStreamExecutor,
                local_path: str,
                remote_base_path: str,
                password: str,
                tracker: ProgressTracker):
    if tracker.skip_file(remote_base_path):
        return

    handled, continued_append_at_part_index = tracker.file_handled(
        local_path, remote_base_path)
    continued_append_at_part_index = continued_append_at_part_index if continued_append_at_part_index > 0 else 0
    if handled:
        return

    stream = get_file_stream(local_path)
    cloud_stream = DefaultUpStream(
        stream, continued_append_starting_at_part_index=continued_append_at_part_index)

    if continued_append_at_part_index > 0:
        seek_stream(stream, continued_append_at_part_index)

    stream_accessor = VersionedCloudStreamAccessor(
        local_path, remote_base_path, cloud_stream)
    if password is not None:
        stream_accessor.add_transform(AES256EncryptTransform(password))

    # metadata_request = MetadataRequest(stream_accessor.get_base_path(), ignore_not_found=True)
    # response = upstreamer.request_executor.execute_request(metadata_request)
    # if response.status_code != 404:
    #     return
    # TODO: handle overwrite if version with same hash already exists
    # TODO: implement continued_append_starting_at_part_index
    # TODO: continued append may loose state in versionedstreamaccessor for parts array
    upstreamer.upload_stream(stream_accessor)
    tracker.track_progress(local_path, remote_base_path)
