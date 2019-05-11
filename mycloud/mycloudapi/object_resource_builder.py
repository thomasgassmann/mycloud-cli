import os
from mycloud.constants import BASE_DIR, AES_EXTENSION, REPLACEMENT_TABLE


class ObjectResourceBuilder:
    def __init__(self, base_dir: str, mycloud_backup_dir: str):
        self.base_dir = base_dir
        self.mycloud_dir = mycloud_backup_dir
        if not self.mycloud_dir.startswith(BASE_DIR):
            raise ValueError('Backup directory must start with /Drive/')
        if not self.mycloud_dir.endswith('/'):
            self.mycloud_dir += '/'
        if not self.base_dir.endswith(os.sep):
            self.base_dir = self.base_dir + os.sep

    @staticmethod
    def combine_cloud_path(left: str, right: str):
        left = ObjectResourceBuilder._replace_invalid_characters(left)
        right = ObjectResourceBuilder._replace_invalid_characters(right)
        if left.endswith('/'):
            left = left[:-1]

        if right.startswith('/'):
            right = right[1:]

        return left + '/' + right

    @staticmethod
    def correct_suffix_sep(remote_path: str, is_file: bool):
        if is_file and remote_path.endswith('/'):
            remote_path = remote_path[:-1]
        if not is_file and not remote_path.endswith('/'):
            remote_path += '/'
        return remote_path

    def build_local_file(self, mycloud_path: str, remove_extension: bool = True):
        path = mycloud_path[len(self.mycloud_dir):]
        normalized_relative_path = os.path.normpath(path)
        if normalized_relative_path == '.':
            normalized_relative_path = os.path.basename(
                mycloud_path if not mycloud_path.endswith('/') else mycloud_path[:-1])
        if remove_extension:
            normalized_relative_path = self.remove_aes_extension(
                normalized_relative_path)

        return os.path.join(self.base_dir, normalized_relative_path)

    @staticmethod
    def ends_with_aes_extension(mycloud_path: str):
        return mycloud_path.endswith(AES_EXTENSION)

    @staticmethod
    def remove_aes_extension(mycloud_path: str):
        if mycloud_path.endswith(AES_EXTENSION):
            mycloud_path = mycloud_path[:-len(AES_EXTENSION)]
        return mycloud_path

    def build_remote_file(self, full_file_path: str):
        file_name = os.path.basename(full_file_path)
        directory = os.path.dirname(full_file_path)
        built = self._build_remote_directory(directory)
        built = ObjectResourceBuilder._replace_invalid_characters(built)
        file_name = ObjectResourceBuilder._replace_invalid_characters(
            file_name)
        return (built + file_name).replace('//', '/')

    def _build_remote_directory(self, directory_path: str):
        base_dir = self.base_dir[:-1]
        if directory_path.startswith(base_dir):
            directory_path = directory_path.replace(base_dir, '', 1)
        directory_path = directory_path.replace('\\', '/')
        if directory_path.startswith('/'):
            directory_path = directory_path[1:]
        if not directory_path.endswith('/'):
            directory_path = directory_path + '/'
        return (self.mycloud_dir + directory_path).replace('//', '/')

    @staticmethod
    def _replace_invalid_characters(string: str):
        for characters in REPLACEMENT_TABLE:
            if characters['character'] in string:
                string = string.replace(
                    characters['character'], characters['replacement'])
        return string

    @staticmethod
    def _is_int(potential_int):
        try:
            int(potential_int)
            return True
        except ValueError:
            return False
