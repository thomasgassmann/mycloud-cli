from filesync.progress import ProgressTracker


class NoProgressTracker(ProgressTracker):
    def __init__(self):
        super().__init__()

    def file_handled(self, file_path, cloud_name):
        return True, -1

    def track_progress(self, file_path, cloud_name):
        pass
