import os
from mycloud.constants import METADATA_FILE_NAME, PARTIAL_EXTENSION, START_NUMBER_LENGTH
from mycloud.helper import is_int
from mycloud.logger import log


class RelativeFileTree:

    def __init__(self):
        self._filedircontainers = {}

    def add_file(self, path: str):
        above = os.path.dirname(path)
        current = path
        while above != current:
            container = self._get_container(above)
            if current == path:
                container.add_file(current)
            elif above != current:
                container.add_dir(current)
            current = above
            above = os.path.dirname(current)

    def loop(self):
        for container_key in self._filedircontainers:
            base_container = self._filedircontainers[container_key]
            prev = None
            cur_key = container_key
            skip = False
            while prev != cur_key:
                prev = cur_key
                cur_key = os.path.dirname(cur_key)
                if prev in self._filedircontainers:
                    container = self._filedircontainers[prev]
                    generator = RelativeFileTree.get_directory_generator(
                        container.files, container.dirs)
                    skip = not next(generator)
                    if skip:
                        break

            base_generator = RelativeFileTree.get_directory_generator(
                base_container.files, base_container.dirs)
            definitely_continue = next(base_generator)
            if not skip and definitely_continue:
                yield from base_generator

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
        if len(files) == 1 and os.path.basename(files[0]) == METADATA_FILE_NAME and len(dirs) > 0:
            metadata_path = files[0]
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
        if len(files) == 0 or not all([PARTIAL_EXTENSION in file for file in base_names]):
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

    def add_dir(self, dir: str):
        if dir not in self.dirs:
            self.dirs.append(dir)
