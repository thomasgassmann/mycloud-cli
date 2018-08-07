import json
from mycloud.constants import MY_CLOUD_BIG_FILE_CHUNK_SIZE
from mycloud.filesync.progress.progress_tracker import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder, MetadataRequest


class LazyCloudProgressTracker(ProgressTracker):
    def __init__(self, request_executor: MyCloudRequestExecutor):
        super().__init__()
        self._request_executor = request_executor

    def track_progress(self, local_file: str, remote_file: str, version: str):
        return

    def file_handled(self, local_file: str, remote_file: str, version: str):
        full_path = ObjectResourceBuilder.combine_cloud_path(
            remote_file, version + '/')
        request = MetadataRequest(full_path, ignore_not_found=True)
        response = self._request_executor.execute_request(request)

        def is_int(val):
            try:
                int(val)
                return True
            except ValueError:
                return False

        if response.status_code == 404:
            return []

        response_json = json.loads(response.text)
        all_parts = [str(item['Path']) for item in response_json['Files']]
        all_names = [str(item['Name']).replace(str(item['Extension']), '')
                     for item in response_json['Files']]
        all_ints = all([is_int(name) for name in all_names])
        if not all_ints:
            raise ValueError('All files in directory must be partial')
        return all_parts
