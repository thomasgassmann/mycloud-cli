import os
from mycloudapi.object_resource_builder import ObjectResourceBuilder
from mycloudapi.object_request import ObjectRequest
from progress_tracker import ProgressTracker
from encryption import Encryptor
from threading import Thread


my_cloud_max_file_size = 3000000000
my_cloud_big_file_chunk_size = 2500000000
encryption_chunk_length = 1024


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
        encryptor = Encryptor(encryption_password, encryption_chunk_length)

    # Perform chunking if file is too big for myCloud
    file_size = os.path.getsize(full_file_path)
    if file_size > my_cloud_max_file_size:
        print(f'Chunking file {cloud_name} because it\'s bigger than the maximum allowed file size')
        read_length = 0
        current_file = 0
        with open(full_file_path, 'rb') as f:
            sent_final = False
            while not sent_final:
                def generator():
                    encryptor = None
                    if is_encrypted:
                        encryptor = Encryptor(encryption_password, encryption_chunk_length)
                    while read_length < my_cloud_big_file_chunk_size:
                        data = f.read(encryption_chunk_length)
                        (final, data_to_be_sent) = __get_chunk(encryptor, data)
                        read_length += encryption_chunk_length
                        yield return data_to_be_sent
                        if final and not sent_final:
                            sent_final = True
                            break
                    if not sent_final:
                        (_, data_to_be_sent) = __get_chunk(encryptor, None)
                        yield return data_to_be_sent
                read_length = 0
                partial_cloud_name = __build_partial_file_upload_name(cloud_name, current_file)
                request = ObjectRequest(partial_cloud_name, bearer_token)
                current_file += 1
                request.put(generator())
    else:
        print(f'Uploading file {full_file_path} to {cloud_name}...')
        __upload_single_file(bearer, full_file_path, cloud_name, encryptor)
        print(f'Uploaded file {full_file_path} to {cloud_name}...')


def __upload_single_file(bearer, full_file_path, cloud_name, encryptor: Encryptor):
    request = ObjectRequest(cloud_name, bearer)
    def log(chunk_num):
        print(f'{cloud_name}: Uploading chunk {chunk_num}...')
    with open(full_file_path, 'rb') as f:
        generator = __get_generator_for_upload(f, encryptor, log)
        request.put(generator)


def __build_partial_file_upload_name(cloud_name, current_iteration):
    file = os.path.basename(cloud_name)
    if not cloud_name.endswith('/'):
        cloud_name += '/'
    return cloud_name + str(current_iteration) + file


def __get_generator_for_upload(file_stream, encryptor: Encryptor, log):
    chunk_num = 0
    while True:
        data = file_stream.read(encryption_chunk_length)
        (final, data_to_be_sent) = __get_chunk(encryptor, data)
        if chunk_num % 1000 == 0:
            log(chunk_num)
        chunk_num += 1
        yield data
        if final:
            break


def __get_chunk(encryptor: Encryptor, data):
    is_encrypted = True
    if encryptor is None:
        is_encrypted = False

    final = False
    if not data:
        if is_encrypted:
            final = True
            data = encryptor.encrypt(bytes([]), last_block=True)
    if is_encrypted:
        if len(data) != encryption_chunk_length:
            final = True
            data = encryptor.encrypt(data, last_block=True)
        else:
            data = encryptor.encrypt(data)
    return (final, data)