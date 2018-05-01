import os, io
from io import BytesIO
from threading import Thread
from mycloudapi import ObjectResourceBuilder, ObjectRequest
from progress import ProgressTracker
from encryption import Encryptor
from helper import FileChunker, SyncBase
from constants import ENCRYPTION_CHUNK_LENGTH


class Uploader(SyncBase):
    def __init__(self, bearer: str, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, encryption_password: str = None):
        super().__init__(bearer, local_directory, mycloud_directory, tracker, encryption_password)


    def upload(self):
        for root, _, files in os.walk(self.local_directory):
            for file in files:
                full_file_path = os.path.join(root, file)
                cloud_file_path = self.builder.build(full_file_path)
                try:
                    if self.progress_tracker.skip_file(full_file_path) or self.progress_tracker.file_handled(full_file_path, cloud_file_path):
                        print(f'Skipping file {full_file_path}...')
                        continue

                    if self.builder.is_partial_file_local_path(full_file_path):
                        print(f'Chunking file {full_file_path}...')
                        self.__upload_in_chunks(full_file_path)
                    else:
                        self.__upload(full_file_path)
                    self.progress_tracker.track_progress(full_file_path, cloud_file_path)
                    self.progress_tracker.try_save()
                except Exception as ex:
                    print(f'ERR: Could not upload file {full_file_path} to {cloud_file_path}!')
    

    def __upload_in_chunks(self, full_file_path: str):
        chunker = FileChunker(full_file_path)
        last = False
        iteration = 0
        while True:
            partial_cloud_name = self.builder.build_partial(full_file_path, iteration)
            (_, partial_local_path) = self.builder.build_partial_local_path(partial_cloud_name)
            print(f'Uploading chunk {iteration} of file {full_file_path} to {partial_cloud_name}...')
            chunk = chunker.get_next_chunk()
            iteration += 1
            if chunk is None:
                break
            if self.progress_tracker.file_handled(full_file_path, partial_cloud_name):
                print(f'Skipping partial file {partial_cloud_name}...')
                continue
            self.__upload_stream(chunk, partial_cloud_name)
            self.progress_tracker.track_progress(partial_local_path, partial_cloud_name)
            self.progress_tracker.try_save()
        chunker.close()


    def __upload(self, full_file_path: str):
        with open(full_file_path, 'rb') as stream:
            cloud_file_name = self.builder.build(full_file_path)
            self.__upload_stream(stream, cloud_file_name)


    def __upload_stream(self, stream, cloud_file_name):
        print(f'Uploading to {cloud_file_name}...')
        self.update_encryptor()
        request = ObjectRequest(cloud_file_name, self.bearer_token)
        generator = self.__get_generator_for_upload(stream)
        request.put(generator)


    def __get_generator_for_upload(self, file_stream):
        last_chunk = None
        chunk_num = 0
        while True:
            if last_chunk is None:
                last_chunk = file_stream.read(ENCRYPTION_CHUNK_LENGTH)
                continue
            if self.is_encrypted:
                last_chunk = self.encryptor.encrypt(last_chunk)
            yield last_chunk
            if chunk_num % 1000 == 0:
                print(f'Uploading chunk {chunk_num}...')
            chunk_num += 1
            last_chunk = file_stream.read(ENCRYPTION_CHUNK_LENGTH)
            if last_chunk == b'' or last_chunk is None or len(last_chunk) < ENCRYPTION_CHUNK_LENGTH:
                break
        final_chunk = last_chunk
        if final_chunk is None:
            final_chunk = bytes([])
        if self.is_encrypted:
            final_chunk = self.encryptor.encrypt(final_chunk, last_block=True)
        if len(final_chunk) > 0:
            yield final_chunk