from mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder
from filesync.progress.progress_tracker import ProgressTracker
from streamapi import DefaultDownStream, DownStreamExecutor, ProgressReporter


def download(request_executor: MyCloudRequestExecutor,
             local_directory: str,
             tracker: ProgressTracker,
             decryption_password: str,
             builder: ObjectResourceBuilder):
    pass


def download_file(upstreamer: UpStreamExecutor,
                  local_path: str,
                  remote_base_path: str,
                  password: str,
                  tracker: ProgressTracker):
    pass
