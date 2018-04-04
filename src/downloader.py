import os, numpy, traceback
from mycloudapi.object_resource_builder import ObjectResourceBuilder
from mycloudapi.object_request import ObjectRequest
from mycloudapi.metadata_request import MetadataRequest
from progress_tracker import ProgressTracker
from encryption import Encryptor


def download(bearer: str, local_directory: str, mycloud_directory: str, progress_file: str, is_encrypted: bool, encryption_password: str):
    if not os.path.isdir(local_directory):
        os.makedirs(local_directory)
    
    tracker = ProgressTracker(progress_file)
    tracker.load_if_exists()
    builder = ObjectResourceBuilder(local_directory, mycloud_directory, is_encrypted)
    errors = []
    files = []
    recurse_directory(files, mycloud_directory, bearer)
    for file in files:
        if tracker.file_handled(file):
            print(f'Skipping file {file}...')
            continue
        try:
            download_path = builder.build_local_path(file)
            directory = os.path.dirname(download_path)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            object_request = ObjectRequest(file, bearer)
            downloaded_content = object_request.get()
            if is_encrypted:
                encryptor = Encryptor(encryption_password, 1024)
            with open(download_path, 'wb') as f:
                last_chunk = None
                for chunk in downloaded_content.iter_content(chunk_size=1024):
                    if last_chunk is None:
                        last_chunk = chunk
                        continue
                    if is_encrypted:
                        last_chunk = encryptor.decrypt(last_chunk)
                    f.write(last_chunk)
                    last_chunk = chunk
                final_chunk = last_chunk
                if is_encrypted:
                    final_chunk = encryptor.decrypt(final_chunk, last_block=True)
                f.write(final_chunk)                        

            tracker.track_progress(file)
            print(f'Downloaded file {file} to {download_path}...')
        except Exception as e:
            err = f'Could not download {file} because: {str(e)}'
            print(err)
            errors.append(err)
        
    for error in errors:
        print(f'ERR: {error}')
    if len(errors) == 0:
        print('Successfully downloaded files')


def recurse_directory(files, mycloud_directory: str, bearer: str):
    print(f'Listing directory {mycloud_directory}...')
    metadata_request = MetadataRequest(mycloud_directory, bearer)
    try:
        (directories, fetched_files) = metadata_request.get_contents()
        for directory in directories:
            recurse_directory(files, directory, bearer)
        for file in fetched_files:
            files.append(file)
    except Exception as e:
        print(f'Failed to list directory: {mycloud_directory}: {str(e)}')