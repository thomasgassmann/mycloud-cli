import os, numpy
from mycloudapi import ObjectResourceBuilder, ObjectResourceBuilder, MetadataRequest, ObjectRequest
from progress import ProgressTracker
from encryption import Encryptor
from helper import SyncBase
from constants import ENCRYPTION_CHUNK_LENGTH
from logger import log


class Downloader(SyncBase):
    def __init__(self, bearer: str, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, encryption_password: str = None):
        super().__init__(bearer, local_directory, mycloud_directory, tracker, encryption_password)
        self.partial_ignores = []
        

    def download(self):
        self.__initialize()
        for chunked, files in self.__list_files(self.mycloud_directory):
            if chunked:
                dictionary = {}
                for file in files:
                    (chunk_number, file_name) = self.builder.build_partial_local_path(file)
                    dictionary[chunk_number] = {'local': file_name, 'cloud': file}
                dictionary = dict(sorted(dictionary.items()))
                first = True
                for key, value in dictionary.items():
                    cloud_path, local_path = value['cloud'], value['local']
                    if self.progress_tracker.file_handled(local_path, cloud_path):
                        log(f'Skipping partial file (Chunk {key}) file {local_path}...')
                        first = False
                        continue
                    if first and os.path.isfile(local_path):
                        log('Removing file...')
                        os.remove(local_path)
                    log(f'Downloading partial file from {cloud_path} to {local_path}, chunk {str(key)}...')
                    try:
                        self.__download_and_append_to(cloud_path, local_path)
                    except Exception as ex:
                        log(f'ERR: Could not download partial file {cloud_path} to {local_path}!')
                        log(f'ERR: Stopping download of partial file!')
                        log(f'ERR: {str(ex)}')
                        break
                    finally:
                        first = False
            else:
                cloud_path = files[0]
                file_name = self.builder.build_local_path(cloud_path)
                log(f'Downloading file {cloud_path} to {file_name}...')
                if self.progress_tracker.skip_file(file_name) or self.progress_tracker.file_handled(file_name, cloud_path):
                    log(f'Skipping file {file_name}...')
                    continue
                try:
                    self.__download_and_append_to(cloud_path, file_name)
                except Exception as ex:
                    log(f'ERR: Could not download file {cloud_path} to {file_name}!')
                    log(f'ERR: {str(ex)}')


    def __download_and_append_to(self, mycloud_path: str, local_file: str):
        directory = os.path.dirname(local_file)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        object_request = ObjectRequest(mycloud_path, self.bearer_token)
        download_stream = object_request.get()
        with open(local_file, 'ab') as file:
            chunk_num = 0
            last_chunk = None
            self.update_encryptor()
            for chunk in download_stream.iter_content(chunk_size=ENCRYPTION_CHUNK_LENGTH):
                if last_chunk is None:
                    last_chunk = chunk
                    continue
                if self.is_encrypted:
                    last_chunk = self.encryptor.decrypt(last_chunk)
                file.write(last_chunk)
                if chunk_num % 1000 == 0:
                    log(f'Downloading chunk {chunk_num} of {mycloud_path}...')
                chunk_num += 1
                last_chunk = chunk
            final_chunk = last_chunk
            if self.is_encrypted:
                final_chunk = self.encryptor.decrypt(final_chunk, last_block=True)
            file.write(final_chunk)
        self.progress_tracker.track_progress(local_file, mycloud_path)
        self.progress_tracker.try_save()


    def __initialize(self):
        if not os.path.isdir(self.local_directory):
            os.makedirs(self.local_directory)


    def __list_files(self, directory):
        base_request = MetadataRequest(directory, self.bearer_token)
        (dirs, files) = base_request.get_contents()
        chunked = True
        if len(dirs) == 0:
            for file in files:
                file_path = file['Path']
                if not self.builder.is_partial_file(file_path):
                    chunked = False
                    
        if chunked:
            file_list = [item['Path'] for item in files]
            for item in file_list:
                self.partial_ignores.append(item)
            yield (True, file_list)

        for file in files:
            if not file['Path'] in self.partial_ignores:
                yield (False, [file['Path']])
        for directory in dirs:
            listed = self.__list_files(directory['Path'])
            for listed_item in listed:
                yield listed_item