import os, numpy
from mycloudapi import ObjectResourceBuilder, ObjectResourceBuilder, MetadataRequest, ObjectRequest
from progress import ProgressTracker
from encryption import Encryptor
from helper import SyncBase, ENCRYPTION_CHUNK_LENGTH


class Downloader(SyncBase):
    def __init__(self, bearer: str, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, encryption_password: str = None):
        super().__init__(bearer, local_directory, mycloud_directory, tracker, encryption_password)
        

    def download(self):
        self.__initialize()
        for chunked, files in self.__list_files(self.mycloud_directory):
            if chunked:
                dictionary = {}
                for file in files:
                    (chunk_number, file_name) = self.builder.build_partial_local_path(file)
                    dictionary[chunk_number] = {'local': file_name, 'cloud': file}
                dictionary = dict(sorted(dictionary.items()))
                for key, value in dictionary.items():
                    cloud_path, local_path = value['cloud'], value['local']
                    if self.progress_tracker.file_handled(local_path, cloud_path):
                        print(f'Skipping partial file (Chunk {key}) file {local_path}...')
                        continue
                    self.__download_and_append_to(cloud_path, local_path)
            else:
                cloud_path = files[0]
                file_name = self.builder.build_local_path(cloud_path)
                if self.progress_tracker.skip_file(file_name) or self.progress_tracker.file_handled(file_name, cloud_path):
                    print(f'Skipping file {file_name}...')
                    continue
                self.__download_and_append_to(cloud_path, file_name)


    def __download_and_append_to(self, mycloud_path: str, local_file: str):
        directory = os.path.dirname(local_file)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        object_request = ObjectRequest(mycloud_path, self.bearer_token)
        download_stream = object_request.get()
        with open(local_file, 'a+b') as file:
            last_chunk = None
            self.update_encryptor()
            for chunk in download_stream.iter_content(chunk_size=ENCRYPTION_CHUNK_LENGTH):
                if last_chunk is None:
                    last_chunk = chunk
                    continue
                if self.is_encrypted:
                    last_chunk = self.encryptor.decrypt(last_chunk)
                file.write(last_chunk)
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
            return (True, file_list)

        for file in files:
            yield (False, [file['Path']])
        for directory in dirs:
            listed = self.__list_files(directory['Path'])
            for listed_item in listed:
                yield listed_item