import json, os, ast, datetime
from filelock import FileLock
from abc import ABCMeta, abstractmethod


class ProgressTracker:
    def __init__(self, progress_file):
        self.progress_file = progress_file
        if not self.progress_file.endswith('.json'):
            self.progress_file += '.json'
        self.files = {}
        self.set_skipped_paths([])


    def track_progress(self, file_path, cloud_name):
        self.files[cloud_name] = os.path.getmtime(file_path)


    def file_handled(self, file_path, cloud_name):
        is_available = cloud_name in self.files.keys()
        if is_available and os.path.isfile(file_path):
            update_date = os.path.getmtime(file_path)
            current_time = self.files[cloud_name]
            if update_date > current_time:
                return False
        return is_available


    @abstractmethod
    def load_if_exists(self):
        raise NotImplementedError


    @abstractmethod
    def load(self):
        raise NotImplementedError


    @abstractmethod
    def save(self):
        raise NotImplementedError


    @abstractmethod
    def try_save(self):
        raise NotImplementedError


    def skip_file(self, file_path):
        for path in self.skipped:
            if file_path.startswith(path):
                return True
        return False
        

    def set_skipped_paths(self, skipped_paths):
        self.skipped = skipped_paths