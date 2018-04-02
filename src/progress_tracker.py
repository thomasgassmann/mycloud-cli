import json, os, ast


class ProgressTracker:
    def __init__(self, progress_file):
        self.progress_file = progress_file
        if not self.progress_file.endswith('.json'):
            self.progress_file += '.json'
        self.files = []

    
    def track_progress(self, file_path):
        normed_path = os.path.normpath(file_path)
        self.files.append(normed_path)


    def load_if_exists(self):
        if os.path.isfile(self.progress_file):
            self.load()


    def file_handled(self, file_path):
        normed_path = os.path.normpath(file_path)
        return normed_path in map(os.path.normpath, self.files)


    def load(self):
        with open(self.progress_file, 'r') as r:
            self.files = json.load(r)


    def save(self):
        with open(self.progress_file, 'w') as fp:
            json.dump(self.files, fp)