import os
from mycloudapi.object_resource_builder import ObjectResourceBuilder
from mycloudapi.object_request import ObjectRequest
from progress_tracker import ProgressTracker
from encryption import Encryptor


def upload(bearer: str, local_directory: str, mycloud_directory: str, progress_file: str, is_encrypted: bool, encryption_password: str):
    if not os.path.isdir(local_directory):
        return
    
    tracker = ProgressTracker(progress_file)
    tracker.load_if_exists()
    builder = ObjectResourceBuilder(local_directory, mycloud_directory, is_encrypted)
    errors = []
    for root, _, files in os.walk(local_directory):
        for file in files:
            try:    
                cloud_name = builder.build(full_file_path)
                full_file_path = os.path.join(root, file)
                if tracker.file_handled(full_file_path, cloud_name):
                    print(f'Skipping file {full_file_path}...')
                    continue
                __upload_single(bearer, full_file_path, cloud_name, is_encrypted, encryption_password)
                print(f'Uploaded file {full_file_path} to {cloud_name}...')
                tracker.track_progress(full_file_path, cloud_name)
                tracker.save()
            except Exception as e:
                err = f'Could not upload {full_file_path} because: {str(e)}'
                print(err)
                errors.append(err)
    for error in errors:
        print(f'ERR: {error}')
    if len(errors) == 0:
        print('Successfully uploaded files')


def __upload_single(bearer, full_file_path, cloud_name, is_encrypted, encryption_password):
    if is_encrypted:
        encryptor = Encryptor(encryption_password, 1024)
    request = ObjectRequest(cloud_name, bearer)
    def generator():
        with open(full_file_path, 'rb') as f:
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
                yield data

    request.put(generator())