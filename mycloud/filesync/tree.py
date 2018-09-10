import os
import gc
import psutil
from pympler import asizeof
from mycloud.constants import METADATA_FILE_NAME, PARTIAL_EXTENSION, START_NUMBER_LENGTH
from mycloud.helper import is_int
from mycloud.logger import log


class RelativeFileTree:

    def __init__(self, generator):
        self._file_generator = generator

    def loop(self):
        RelativeFileTree._print_ram_usage()
        for file in self._file_generator:
            path = file['Path']

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

    @staticmethod
    def _print_ram_usage():
        process = psutil.Process(os.getpid())
        log(f'Memory usage: {process.memory_info().rss}')


class ConditionalWriteStorage:

    def __init__(self, max_size):
        self._list_of_objs = []
        self._total_size = 0
        self._max_size = max_size

    def add(self, primitive):
        self._list_of_objs.append(primitive)
        size_of_obj = asizeof.asizeof(primitive)
        self._total_size += size_of_obj
        if self._total_size >= self._max_size:
            self._write_to_storage()

    def get(self):
        pass

    def _write_to_storage(self):
        # TODO: write to temp file
        pass
