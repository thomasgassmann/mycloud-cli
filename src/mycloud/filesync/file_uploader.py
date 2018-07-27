import os, io, time, threading, signal, sys
from io import BytesIO
from sys import platform
from threading import Thread
from progress import ProgressTracker
from helper import operation_timeout
from constants import ENCRYPTION_CHUNK_LENGTH, RETRY_COUNT, SAVE_FREQUENCY
from logger import log
from collections import deque
from random import shuffle
from mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from filesync.versioned_stream_accessor import VersionedCloudStreamAccessor
from streamapi import DefaultUpStream, UpStreamExecutor, ProgressReporter
from streamapi.transforms import AES256EncryptTransform


def get_file_stream(file_path):
    def open_file(dict):
        return open(dict['path'], 'rb')
    stream = operation_timeout(open_file, path=file_path)
    return stream


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
            upload_file(upstreamer, local, remote, encryption_password)
            if current_iteration % SAVE_FREQUENCY == 0:
                tracker.try_save()
            current_iteration += 1
        

def upload_file(upstreamer: UpStreamExecutor, 
                local_path: str,
                remote_base_path: str,
                password: str):
    stream = get_file_stream(local_path)
    cloud_stream = DefaultUpStream(stream, continued_append_starting_at_part_index=0)
    stream_accessor = VersionedCloudStreamAccessor(local_path, remote_base_path, cloud_stream)
    if password is not None:
        stream_accessor.add_transform(AES256EncryptTransform(password))
    # TODO: handle overwrite if version with same hash already exists
    # TODO: implement continued_append_starting_at_part_index
    upstreamer.upload_stream(stream_accessor)
    