import os
import time
from abc import ABC, abstractmethod


# Define API for progress tracking
class ProgressTracker(ABC):
    def __init__(self):
        self.set_skipped_paths([])

    @abstractmethod
    def track_progress(self, file_path: str, cloud_name: str, version: str):
        raise NotImplementedError()

    @abstractmethod
    def file_handled(self, file_path: str, cloud_name: str, version: str):
        raise NotImplementedError()

    def load_if_exists(self):
        pass

    def load(self):
        pass

    def save(self):
        pass

    def try_save(self):
        pass

    def skip_file(self, remote_file_path: str):
        for path in self.skipped:
            if remote_file_path.startswith(path):
                return True
        return False

    def set_skipped_paths(self, skipped_paths):
        self.skipped = skipped_paths
