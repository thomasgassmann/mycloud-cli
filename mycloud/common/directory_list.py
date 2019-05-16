from mycloud.mycloudapi.metadata_request import MetadataRequest


def get_all_files_recursively(request_executor, directory: str):
    metadata_request = MetadataRequest(directory)
    response = request_executor.execute_request(metadata_request)
    (directories, fetched_files) = MetadataRequest.format_response(response)
    for file in fetched_files:
        yield file

    for sub_directory in directories:
        yield from get_all_files_recursively(request_executor, sub_directory['Path'])
