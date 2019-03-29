import os
from mycloud.constants import METADATA_FILE_NAME, PARTIAL_EXTENSION, START_NUMBER_LENGTH
from mycloud.common import is_int


class RelativeFileTree:

    def __init__(self):
        self._filedircontainers = {}
        self._started_loop = False
        self.file_count = 0

    def add_file(self, path: str, base: str):
        above = os.path.dirname(path)
        current = path
        while current not in (above, base):
            container = self._get_container(above)
            if current == path:
                container.add_file(current)
            elif above != current:
                container.add_dir(current)
            current = above
            above = os.path.dirname(current)
        self.file_count += 1

    def loop(self):
        if self._started_loop:
            raise ValueError('Generator may only be called once')

        self._started_loop = True

        def _container_continue(key: str):
            if key not in self._filedircontainers:
                return [False, None]
            container = self._filedircontainers[key]
            base_generator = RelativeFileTree.get_directory_generator(
                container.files, container.dirs)
            return [next(base_generator), base_generator]

        for container_key in self._filedircontainers:
            generator = _container_continue(container_key)
            if generator[0] and _container_continue(os.path.dirname(container_key))[0]:
                yield from generator[1]
            del generator[1]
            del generator[0]
            cont = self._filedircontainers[container_key]
            if not any(cont.dirs):
                del cont.dirs
                del cont.files
                self._filedircontainers[container_key] = None

    def _get_container(self, path: str):
        file_dir_container = None
        if not path in self._filedircontainers:
            file_dir_container = FileDirContainer()
            self._filedircontainers[path] = file_dir_container
        else:
            file_dir_container = self._filedircontainers[path]
        return file_dir_container

    @staticmethod
    def get_directory_generator(files, dirs):
        if len(files) == 1 and os.path.basename(files[0]) == METADATA_FILE_NAME and any(dirs):
            yield False
            return

        partial_directory = RelativeFileTree.is_partial_directory(files)
        yield True
        if partial_directory:
            yield partial_directory, files
        else:
            for file in files:
                yield partial_directory, [file]

    @staticmethod
    def is_partial_directory(files):
        base_names = [os.path.basename(file) for file in files]
        if not any(files) or not all([PARTIAL_EXTENSION in file for file in base_names]):
            return False

        for file in base_names:
            number = file[:START_NUMBER_LENGTH]
            if not is_int(number):
                return False

        return True


class FileDirContainer:

    def __init__(self):
        self.files = []
        self.dirs = []

    def add_file(self, file: str):
        if file not in self.files:
            self.files.append(file)

    def add_dir(self, directory: str):
        if directory not in self.dirs:
            self.dirs.append(directory)
