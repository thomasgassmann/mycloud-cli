from mycloudapi import MetadataRequest, MyCloudRequestExecutor
from logger import log


def recurse_directory(files, mycloud_directory: str, request_executor: MyCloudRequestExecutor, result_properties=None):
    if result_properties is None:
        result_properties = ['Path']
    log(f'Listing directory {mycloud_directory}...')
    metadata_request = MetadataRequest(mycloud_directory)
    try:
        response = request_executor.execute_request(metadata_request)
        (directories, fetched_files) = MetadataRequest.format_response(response)
        for directory in directories:
            recurse_directory(files, directory['Path'], request_executor, result_properties)
        for file in fetched_files:
            if len(result_properties) == 1:
                files.append(file[result_properties[0]])
            else:
                properties = []
                for result_property in result_properties:
                    properties.append(file[result_property])
                files.append(properties)
    except Exception as e:
        log(f'Failed to list directory: {mycloud_directory}: {str(e)}')