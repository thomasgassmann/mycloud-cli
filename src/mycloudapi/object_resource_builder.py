import base64, os


BASE_DIR = '/Drive/'
AES_EXTENSION = '.aes'


class ObjectResourceBuilder:
    def __init__(self, base_dir: str, mycloud_backup_dir: str, encrypted: bool):
        self.base_dir = base_dir
        self.encrypted = encrypted
        self.mycloud_dir = mycloud_backup_dir
        if not self.mycloud_dir.startswith(BASE_DIR):
            raise ValueError('Backup directory must start with /Drive/')
        if not self.mycloud_dir.endswith('/'):
            self.mycloud_dir += '/'


    def build_local_path(self, mycloud_path: str):
        str = mycloud_path[len(self.mycloud_dir):]
        if self.encrypted:
            str = str[:-len(AES_EXTENSION)]
        normalized_relative_path = os.path.normpath(str)
        return os.path.join(self.base_dir, normalized_relative_path)


    def build(self, path: str):
        if os.path.isfile(path):
            return self.build_file(path)
        elif os.path.isdir(path):
            return self.build_directory(path)
        else:
            raise ValueError('Path is neither file, nor directory')


    def build_directory(self, directory_path: str):
        if not os.path.isdir(directory_path):
            raise ValueError(f'Path is not directory: {directory_path}')

        if self.base_dir in directory_path:
            directory_path = directory_path.replace(self.base_dir, '')
        directory_path = directory_path.replace('\\', '/')
        if directory_path.startswith('/'):
            directory_path = directory_path[1:]
        if not directory_path.endswith('/'):
            directory_path = directory_path + '/'
        return (self.mycloud_dir + directory_path).replace('//', '/')


    def build_file(self, full_file_path: str):
        if not os.path.isfile(full_file_path):
            raise ValueError('Path is no file')

        file_name = os.path.basename(full_file_path)
        directory = os.path.dirname(full_file_path)
        if self.encrypted:
            file_name += AES_EXTENSION
        built = self.build_directory(directory)
        return (built + file_name).replace('//', '/')