import os
from mycloudapi.object_resource_builder import ObjectResourceBuilder
from mycloudapi.object_request import ObjectRequest
from progress_tracker import ProgressTracker
from encryption import Encryptor
from threading import Thread


my_cloud_max_file_size = 3000000000
my_cloud_big_file_chunk_size = 2500000000
encryption_chunk = 1024


def upload(bearer: str, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, is_encrypted: bool, encryption_password: str):
    if not os.path.isdir(local_directory):
        return

    builder = ObjectResourceBuilder(local_directory, mycloud_directory, is_encrypted)
    for root, _, files in os.walk(local_directory):
        for file in files:
            try:    
                full_file_path = os.path.join(root, file)
                cloud_name = builder.build(full_file_path)
                if tracker.skip_file(full_file_path) or tracker.file_handled(full_file_path, cloud_name):
                    print(f'Skipping file {full_file_path}...')
                    continue
                __upload(bearer, full_file_path, cloud_name, is_encrypted, encryption_password)
                tracker.track_progress(full_file_path, cloud_name)
                tracker.try_save()
            except Exception as e:
                err = f'Could not upload {full_file_path} because: {str(e)}'
                print(err)


def __upload(bearer, full_file_path, cloud_name, is_encrypted, encryption_password):
    encryptor = None
    if is_encrypted:
        encryptor = Encryptor(encryption_password, encryption_chunk)

    # Perform chunking if file is too big for myCloud
    if os.path.getsize(full_file_path) > my_cloud_max_file_size:
        print(f'Chunking file {cloud_name} because it\'s bigger than the maximum allowed file size')
        read_length = 0
        with open(full_file_path, 'rb') as f:
            while read_length < my_cloud_big_file_chunk_size:


            
    else:
        print(f'Uploading file {full_file_path} to {cloud_name}...')
        __upload_single_file(bearer, full_file_path, cloud_name, is_encrypted, encryption_password)
        print(f'Uploaded file {full_file_path} to {cloud_name}...')


def __upload_single_file(bearer, full_file_path, cloud_name, encryptor: Encryptor):
    request = ObjectRequest(cloud_name, bearer)
    with open(full_file_path, 'rb') as f:
        generator = __get_generator_for_upload(f, encryptor)
        request.put(generator)


def __get_generator_for_upload(file_stream, encryptor: Encryptor):
    is_encrypted = True
    if encryptor is None:
        is_encrypted = False
    chunk_num = 0
    while True:
        data = file_stream.read(encryption_chunk)
        if not data:
            if is_encrypted:
                yield encryptor.encrypt(bytes([]), last_block=True)
                break
        if is_encrypted:
            if len(data) != encryption_chunk:
                yield encryptor.encrypt(data, last_block=True)
                break
            else:
                data = encryptor.encrypt(data)
        if chunk_num % 1000 == 0:
            print(f'{cloud_name}: Uploading chunk {chunk_num}...')
        chunk_num += 1
        yield data