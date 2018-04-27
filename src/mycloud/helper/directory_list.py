from mycloud.mycloudapi.metadata_request import MetadataRequest


def recurse_directory(files, mycloud_directory: str, bearer: str, result_properties=None):
    if result_properties is None:
        result_properties = ['Path']
    print(f'Listing directory {mycloud_directory}...')
    metadata_request = MetadataRequest(mycloud_directory, bearer)
    try:
        (directories, fetched_files) = metadata_request.get_contents()
        for directory in directories:
            recurse_directory(files, directory['Path'], bearer, result_properties)
        for file in fetched_files:
            if len(result_properties) == 1:
                files.append(file[result_properties[0]])
            else:
                properties = []
                for result_property in result_properties:
                    properties.append(file[result_property])
                files.append(properties)
    except Exception as e:
        print(f'Failed to list directory: {mycloud_directory}: {str(e)}')