from mycloud.mycloudapi.requests.drive import MetadataRequest
from mycloud.mycloudapi import MyCloudRequestExecutor


async def get_all_files(request_executor: MyCloudRequestExecutor, directory: str):
    metadata_request = MetadataRequest(directory)
    response = await request_executor.execute_request(metadata_request)
    (directories, fetched_files) = MetadataRequest.format_response(response)
    for file in fetched_files:
        yield file

    for sub_directory in directories:
        async for file in get_all_files(request_executor, sub_directory['Path']):
            yield file
