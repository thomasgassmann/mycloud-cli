import os, io
from io import BytesIO
from threading import Thread
from mycloudapi import ObjectResourceBuilder, ObjectRequest
from progress import ProgressTracker
from encryption import Encryptor
from helper import FileChunker, SyncBase, ENCRYPTION_CHUNK_LENGTH


class Uploader(SyncBase):
    def __init__(self, bearer: str, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, encryption_password: str = None):
        super().__init__(bearer, local_directory, mycloud_directory, tracker, encryption_password)


    def upload(self):
        for root, _, files in os.walk(self.local_directory):
            for file in files:
                full_file_path = os.path.join(root, file)
                cloud_file_path = self.builder.build(full_file_path)
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
    

    def __upload_in_chunks(self, full_file_path: str):
        chunker = FileChunker(full_file_path)
        last = False
        iteration = 0
        while True:
            partial_cloud_name = self.builder.build_partial(full_file_path, iteration)
            partial_local_path = self.builder.build_partial_local_path(partial_cloud_name)
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


    def __upload(self, full_file_path: str):
        with open(full_file_path, 'rb') as stream:
            cloud_file_name = self.builder.build(full_file_path)
            self.__upload_stream(stream, cloud_file_name)


    def __upload_stream(self, stream, cloud_file_name):
        self.update_encryptor()
        request = ObjectRequest(cloud_file_name, self.bearer_token)
        generator = self.__get_generator_for_upload(stream)
        request.put(generator)


    def __get_generator_for_upload(self, file_stream):
        chunk_num = 0
        while True:
            data = file_stream.read(ENCRYPTION_CHUNK_LENGTH)
            if data == b'' or data is None:
                break
            (final, data_to_be_sent) = self.__get_chunk(data)
            chunk_num += 1
            if chunk_num % 1000 == 0:
                print(f'Uploading {chunk_num}...')
            yield data_to_be_sent
            if final:
                break


    def __get_chunk(self, data):
        final = False
        if data is None:
            final = True
            data = self.encryptor.encrypt(bytes([]), last_block=True) if self.is_encrypted else bytes([])
        if self.is_encrypted:
            if len(data) != ENCRYPTION_CHUNK_LENGTH:
                final = True
                data = self.encryptor.encrypt(data, last_block=True)
            else:
                data = self.encryptor.encrypt(data)
        return (final, data)