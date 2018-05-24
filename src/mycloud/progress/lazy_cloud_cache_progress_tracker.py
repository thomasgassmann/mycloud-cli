from progress import ProgressTracker
from progress.lazy_cloud_progress_tracker import LazyCloudProgressTracker
from progress.file_progress_tracker import FileProgressTracker


class LazyCloudCacheProgressTracker(ProgressTracker):
    def __init__(self, bearer, progress_file):
        self.lazy_cloud_progress_tracker = LazyCloudProgressTracker(bearer)
        self.progress_file_tracker = FileProgressTracker(progress_file)
        super().__init__()


    def file_handled(self, file_path, cloud_name):
        return self.progress_file_tracker.file_handled(file_path, cloud_name) or self.lazy_cloud_progress_tracker.file_handled(file_path, cloud_name)


    def load_if_exists(self):
        self.progress_file_tracker.load_if_exists()
        self.lazy_cloud_progress_tracker.load_if_exists()


    def load(self):
        self.progress_file_tracker.load()
        self.lazy_cloud_progress_tracker.load()


    def save(self):
        self.progress_file_tracker.save()
        self.lazy_cloud_progress_tracker.save()


    def try_save(self):
        self.progress_file_tracker.try_save()
        self.lazy_cloud_progress_tracker.try_save()


    def skip_file(self, file_path):
        return self.progress_file_tracker.skip_file(file_path) or self.lazy_cloud_progress_tracker.skip_file(file_path)
        

    def set_skipped_paths(self, skipped_paths):
        self.progress_file_tracker.set_skipped_paths(skipped_paths)
        self.lazy_cloud_progress_tracker.set_skipped_paths(skipped_paths)


    def track_progress(self, file_path, cloud_name):
        self.progress_file_tracker.track_progress(file_path, cloud_name)
        self.lazy_cloud_progress_tracker.track_progress(file_path, cloud_name)