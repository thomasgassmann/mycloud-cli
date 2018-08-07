import os
import time
from abc import ABC, abstractmethod


class ProgressTracker(ABC):
    def __init__(self):
        self.set_skipped_paths([])

    @abstractmethod
    def track_progress(self, local_file: str, remote_file: str, version: str):
        raise NotImplementedError()

    @abstractmethod
    def file_handled(self, local_file: str, remote_file: str, version: str):
        """
            Checks whether a given file was arleady handled.

            Returns a bool indicating whether the item was handled and a list of already uploaded parts for a given version.
        """
        raise NotImplementedError()

    def load_if_exists(self):
        pass

    def try_save(self):
        pass

    def skip_file(self, local_file_path: str):
        return not all([local_file_path.startswith(path) for path in self._skipped])

    def set_skipped_paths(self, skipped_paths):
        self._skipped = skipped_paths
