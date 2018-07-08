import os, io, time, signal
from io import BytesIO
from threading import Thread
from mycloudapi import PutObjectRequest
from progress import ProgressTracker
from encryption import Encryptor
from helper import FileChunker, SyncBase
from constants import ENCRYPTION_CHUNK_LENGTH, RETRY_COUNT, SAVE_FREQUENCY
from logger import log
from collections import deque
from random import shuffle
from mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor


class TimeoutException(Exception):
    pass


class CouldNotReadFileException(Exception):
    pass


class Uploader(SyncBase):
    def __init__(self, request_executor: MyCloudRequestExecutor, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, encryption_password: str, builder: ObjectResourceBuilder):
        super().__init__(request_executor, local_directory, mycloud_directory, tracker, encryption_password, builder)


    def upload(self):
        failed_uploads = deque()
        def do_upload(root, file, retry=0):
            full_file_path = os.path.join(root, file)
            cloud_file_path = self.builder.build(full_file_path)
            try:
                if self.progress_tracker.skip_file(full_file_path) or self.progress_tracker.file_handled(full_file_path, cloud_file_path):
                    log(f'Skipping file {full_file_path}...')
                    self.progress_tracker.track_progress(full_file_path, cloud_file_path)
                    return

                if self.builder.is_partial_file_local_path(full_file_path):
                    log(f'Chunking file {full_file_path}...')
                    self._upload_in_chunks(full_file_path)
                else:
                    self._upload(full_file_path)
                self.progress_tracker.track_progress(full_file_path, cloud_file_path)
            except Exception as ex:
                log(f'Could not upload file {full_file_path} to {cloud_file_path}!', error=True)
                log(str(ex), error=True)
                failed_uploads.append((root, file, retry))
        def upload_single_failed():
            if len(failed_uploads) > 0:
                (root, file, i) = failed_uploads.popleft()
                log(f'Retrying to upload failed file {os.path.join(root, file)}...')
                if i < RETRY_COUNT:
                    i += 1
                    do_upload(root, file, i)
        current_iteration = 0
        for root, dirs, files in os.walk(self.local_directory, topdown=True):
            shuffle(dirs)
            for file in files:
                do_upload(root, file)
                current_iteration += 1
                if current_iteration % SAVE_FREQUENCY == 0:
                    self.progress_tracker.try_save()
            upload_single_failed()
        for _ in range(len(failed_uploads)):
            upload_single_failed()
    

    def _upload_in_chunks(self, full_file_path: str):
        chunker = FileChunker(full_file_path)
        last = False
        iteration = 0
        while True:
            partial_cloud_name = self.builder.build_partial(full_file_path, iteration)
            (_, partial_local_path) = self.builder.build_partial_local_path(partial_cloud_name)
            log(f'Uploading chunk {iteration} of file {full_file_path} to {partial_cloud_name}...')
            chunk = chunker.get_next_chunk()
            iteration += 1
            if chunk is None:
                break
            if self.progress_tracker.file_handled(full_file_path, partial_cloud_name):
                log(f'Skipping partial file {partial_cloud_name}...')
                continue
            self._upload_stream(chunk, partial_cloud_name)
            self.progress_tracker.track_progress(partial_local_path, partial_cloud_name)
            self.progress_tracker.try_save()
        chunker.close()


    def _upload(self, full_file_path: str):
        stream = open(full_file_path, 'rb')
        cloud_file_name = self.builder.build(full_file_path)
        self._upload_stream(stream, cloud_file_name)
        stream.close()


    def _upload_stream(self, stream, cloud_file_name):
        log(f'Uploading to {cloud_file_name}...')
        self.update_encryptor()
        generator = self._get_generator_for_upload(stream)
        request = PutObjectRequest(cloud_file_name, generator)
        _ = self.request_executor.execute_request(request)


    def _get_generator_for_upload(self, file_stream):
        last_chunk = None
        chunk_num = 0

        bytes_per_second = 0
        current_time = time.time()
        read_since_time_calculation = 0

        while True:
            if last_chunk is None:
                last_chunk = Uploader._safe_file_stream_read(file_stream, ENCRYPTION_CHUNK_LENGTH)
                continue
            if self.is_encrypted:
                last_chunk = self.encryptor.encrypt(last_chunk, last_block=True) if len(last_chunk) != ENCRYPTION_CHUNK_LENGTH else self.encryptor.encrypt(last_chunk)
            yield last_chunk
            if chunk_num % 1000 == 0:
                log(f'Uploading iteration {chunk_num} and byte {str(chunk_num * ENCRYPTION_CHUNK_LENGTH)} ({str(bytes_per_second)} bytes per second)...')
            chunk_num += 1
            last_chunk = file_stream.read(ENCRYPTION_CHUNK_LENGTH)
            if last_chunk == b'' or last_chunk is None or len(last_chunk) < ENCRYPTION_CHUNK_LENGTH:
                break
            
            read_since_time_calculation += len(last_chunk)
            read_time = time.time()
            if read_time - current_time > 1:
                time_passed = read_time - current_time
                bytes_per_second = int(read_since_time_calculation / time_passed)
                read_since_time_calculation = 0
                current_time = time.time()

        final_chunk = last_chunk
        if final_chunk is None:
            final_chunk = bytes([])
        if self.is_encrypted:
            final_chunk = self.encryptor.encrypt(final_chunk, last_block=True)
        if len(final_chunk) > 0:
            yield final_chunk

    
    @staticmethod
    def _safe_file_stream_read(file_stream, length):

        def timeout_handler(signum, frame):
            raise TimeoutException

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(15)
        try:
            result = file_stream.read(length)
        except TimeoutException:
            signal.alarm(0)
            log('Could not read file in time', error=True)
            raise CouldNotReadFileException

        signal.alarm(0)
        return result