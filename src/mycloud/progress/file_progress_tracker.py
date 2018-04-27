import json, os, ast, datetime
from filelock import FileLock
from progress_tracker import ProgressTracker


class FileProgressTracker(ProgressTracker):
    def __init__(self, progress_file):
        self.progress_file = progress_file
        if not self.progress_file.endswith('.json'):
            self.progress_file += '.json'
        super().__init__()


    def load_if_exists(self):
        if os.path.isfile(self.progress_file):
            self.load()


    def load(self):
        with open(self.progress_file, 'r') as r:
            self.files = json.load(r)


    def save(self):
        real = self.progress_file
        bak = self.progress_file + '.bak'
        tmp = self.progress_file + '.tmp'
        with open(tmp, 'w') as fp:
            json.dump(self.files, fp)
        if os.path.isfile(real):
            os.rename(real, bak)
        os.rename(tmp, real)
        if os.path.isfile(bak):
            os.remove(bak)


    def try_save(self):
        try:
            self.save()
        except Exception as e:
            print(f'Could not save file because: {str(e)}')