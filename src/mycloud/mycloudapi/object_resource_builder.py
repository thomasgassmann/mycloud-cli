import base64, os, re
from constants import PARTIAL_EXTENSION, START_NUMBER_LENGTH, AES_EXTENSION, MY_CLOUD_MAX_FILE_SIZE, BASE_DIR


class ObjectResourceBuilder:
    def __init__(self, base_dir: str, mycloud_backup_dir: str, encrypted: bool):
        self.base_dir = base_dir
        self.encrypted = encrypted
        self.mycloud_dir = mycloud_backup_dir
        if not self.mycloud_dir.startswith(BASE_DIR):
            raise ValueError('Backup directory must start with /Drive/')
        if not self.mycloud_dir.endswith('/'):
            self.mycloud_dir += '/'


    def build_partial(self, path: str, current_iteration: int):
        formatted_iteration = format(current_iteration, f'0{START_NUMBER_LENGTH}d')
        directory = os.path.dirname(path)
        file_name = os.path.basename(path)
        updated_file_name = f'{formatted_iteration}-{file_name}{PARTIAL_EXTENSION}'
        joined = os.path.join(directory, file_name, updated_file_name)
        self.build_file(joined)
        cloud_path = self.build_file(joined)
        return cloud_path


    def is_partial_file_local_path(self, path: str):
        file_size = os.path.getsize(path)
        return file_size >= MY_CLOUD_MAX_FILE_SIZE


    def is_partial_file(self, mycloud_path: str):
        unencrypted_mycloud_pathcloud = self.__remove_encryption_file_name_if_exists(mycloud_path)
        ends_wtih_partial = unencrypted_mycloud_pathcloud.endswith(PARTIAL_EXTENSION)
        file_name = os.path.basename(mycloud_path)
        start_number = file_name[:START_NUMBER_LENGTH]
        starts_with_dash = file_name[START_NUMBER_LENGTH:].startswith('-')
        is_integer = ObjectResourceBuilder.__is_int(start_number)
        return is_integer and ends_wtih_partial and starts_with_dash


    def build_partial_local_path(self, mycloud_path: str):
        if not self.is_partial_file(mycloud_path):
            return self.build_local_path(mycloud_path)
        unencrypted_cloud_path = self.__remove_encryption_file_name_if_exists(mycloud_path)
        numbers_to_cut = START_NUMBER_LENGTH + 1 # +1 for dash
        file_name = os.path.basename(mycloud_path)
        chunk_number = int(file_name[:START_NUMBER_LENGTH])
        dir = os.path.dirname(mycloud_path)
        if self.encrypted:
            dir += AES_EXTENSION
        local_path = self.build_local_path(dir)
        return (chunk_number, local_path)


    def build_local_path(self, mycloud_path: str):
        mycloud_path = self.__remove_encryption_file_name_if_exists(mycloud_path)
        str = mycloud_path[len(self.mycloud_dir):]
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
        if directory_path.startswith(self.base_dir):
            directory_path = directory_path.replace(self.base_dir, '', 1)
        directory_path = directory_path.replace('\\', '/')
        if directory_path.startswith('/'):
            directory_path = directory_path[1:]
        if not directory_path.endswith('/'):
            directory_path = directory_path + '/'
        return (self.mycloud_dir + directory_path).replace('//', '/')


    def build_file(self, full_file_path: str):
        file_name = os.path.basename(full_file_path)
        directory = os.path.dirname(full_file_path)
        if self.encrypted:
            file_name += AES_EXTENSION
        built = self.build_directory(directory)
        return (built + file_name).replace('//', '/')

    
    def __remove_encryption_file_name_if_exists(self, mycloud_file_name):
        if self.encrypted:
            return mycloud_file_name[:-len(AES_EXTENSION)]
        return mycloud_file_name


    @staticmethod
    def __is_int(s):
        try: 
            int(s)
            return True
        except ValueError:
            return False