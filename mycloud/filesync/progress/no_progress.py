from mycloud.filesync.progress.progress_tracker import ProgressTracker


class NoProgressTracker(ProgressTracker):
    def __init__(self):
        super().__init__()

    def track_progress(self, local_file: str, remote_file: str, version: str):
        return

    def file_handled(self, local_file: str, remote_file: str, version: str):
        return []
