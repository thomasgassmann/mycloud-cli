from mycloud.mycloudapi.requests import MetadataRequest
from mycloud.mycloudapi import MyCloudRequestExecutor


def get_all_files_recursively(request_executor: MyCloudRequestExecutor, directory: str):
    metadata_request = MetadataRequest(directory)
    response = request_executor.execute_request(metadata_request)
    (directories, fetched_files) = MetadataRequest.format_response(response)
    for file in fetched_files:
        yield file

    for cur_dir in directories:
        yield from get_all_files_recursively(request_executor, cur_dir['Path'])
