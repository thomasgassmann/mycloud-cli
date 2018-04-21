import os, numpy
from mycloudapi.object_resource_builder import ObjectResourceBuilder
from mycloudapi.object_request import ObjectRequest
from progress_tracker import ProgressTracker
from encryption import Encryptor
from directory_list import recurse_directory


def download(bearer: str, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, is_encrypted: bool, encryption_password: str):
    if not os.path.isdir(local_directory):
        os.makedirs(local_directory)
    
    builder = ObjectResourceBuilder(local_directory, mycloud_directory, is_encrypted)
    errors = []
    files = []
    # TODO: list is lazily and immediately download files
    recurse_directory(files, mycloud_directory, bearer)
    for file in files:
        try:
            download_path = builder.build_local_path(file)
            if tracker.file_handled(download_path, file) or tracker.skip_file(file):
                print(f'Skipping file {file}...')
                continue
            directory = os.path.dirname(download_path)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            object_request = ObjectRequest(file, bearer)
            print(f'Downloading file {file} to {download_path}...')
            downloaded_content = object_request.get()
            if is_encrypted:
                encryptor = Encryptor(encryption_password, 1024)
            with open(download_path, 'wb') as f:
                last_chunk = None
                chunk_num = 1
                for chunk in downloaded_content.iter_content(chunk_size=1024):
                    if last_chunk is None:
                        last_chunk = chunk
                        continue
                    if is_encrypted:
                        last_chunk = encryptor.decrypt(last_chunk)
                    if chunk_num % 10000 == 0:
                        print(f'Uploading chunk {chunk_num}...')
                    f.write(last_chunk)
                    chunk_num += 1
                    last_chunk = chunk
                final_chunk = last_chunk
                if is_encrypted:
                    final_chunk = encryptor.decrypt(final_chunk, last_block=True)
                f.write(final_chunk)                        

            tracker.track_progress(download_path, file)
            tracker.try_save()
            print(f'Downloaded file {file} to {download_path}...')
        except Exception as e:
            err = f'Could not download {file} because: {str(e)}'
            print(err)
            errors.append(err)
        
    for error in errors:
        print(f'ERR: {error}')
    if len(errors) == 0:
        print('Successfully downloaded files')