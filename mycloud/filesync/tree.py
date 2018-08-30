import os


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
            container = self._filedircontainers[container_key]
            yield (container.dirs, container.files)

    def _get_container(self, path: str):
        file_dir_container = None
        if not path in self._filedircontainers:
            file_dir_container = FileDirContainer()
            self._filedircontainers[path] = file_dir_container
        else:
            file_dir_container = self._filedircontainers[path]
        return file_dir_container


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
