from mycloudapi import MyCloudRequestExecutor, MetadataRequest
from logger import log
import sys, os
from hurry.filesize import size


def calculate_size(request_executor: MyCloudRequestExecutor, directory: str):
    original_out = sys.stdout
    sys.stdout = None
    summed_up = 0
    longest_string = 0
    file_count = 0
    for file in file_generator(request_executor, directory):
        file_count += 1
        original_out.write(str(' ' * longest_string) + '\r')
        to_print = f'Bytes: {summed_up} | Size (readable): {size(summed_up)} | Count: {file_count}'
        if len(to_print) > longest_string:
            longest_string = len(to_print)

        original_out.write(to_print)
        summed_up += int(file['Length'])

    sys.stdout = original_out


def file_generator(request_executor: MyCloudRequestExecutor, directory: str):
    metadata_request = MetadataRequest(directory)
    response = request_executor.execute_request(metadata_request)
    (directories, fetched_files) = MetadataRequest.format_response(response)
    for file in fetched_files:
        yield file
    
    for directory in directories:
        yield from file_generator(request_executor, directory['Path'])