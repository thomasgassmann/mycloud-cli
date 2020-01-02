class ProgressTracker:

    def __init__(self):
        self.set_skipped_paths([])

    def skip_file(self, file_path: str):
        return not all([file_path.startswith(path) for path in self._skipped])

    def set_skipped_paths(self, skipped_paths):
        self._skipped = skipped_paths
