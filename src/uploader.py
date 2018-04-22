import os
from mycloudapi.object_resource_builder import ObjectResourceBuilder
from mycloudapi.object_request import ObjectRequest
from progress_tracker import ProgressTracker
from encryption import Encryptor
from threading import Thread


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
    print(f'Uploading file {full_file_path} to {cloud_name}...')
    __upload_single(bearer, full_file_path, cloud_name, is_encrypted, encryption_password)
    print(f'Uploaded file {full_file_path} to {cloud_name}...')


def __upload_single(bearer, full_file_path, cloud_name, is_encrypted, encryption_password):
    if is_encrypted:
        encryptor = Encryptor(encryption_password, 1024)
    request = ObjectRequest(cloud_name, bearer)
    def generator():
        with open(full_file_path, 'rb') as f:
            chunk_num = 1
            while True:
                data = f.read(1024)
                if not data:
                    if is_encrypted:
                        yield encryptor.encrypt(bytes([]), last_block=True)
                    break
                if is_encrypted:
                    if len(data) != 1024:
                        yield encryptor.encrypt(data, last_block=True)
                        break
                    else:
                        data = encryptor.encrypt(data)
                if chunk_num % 1000 == 0:
                    print(f'{cloud_name}: Uploading chunk {chunk_num}...')
                chunk_num += 1
                yield data

    request.put(generator())