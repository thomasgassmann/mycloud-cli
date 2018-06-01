import argparse, os, sys, json
from upload import Uploader
from download import Downloader
from mycloudapi import get_bearer_token, ObjectResourceBuilder
from progress import ProgressTracker, LazyCloudProgressTracker, FileProgressTracker, CloudProgressTracker, NoProgressTracker, LazyCloudCacheProgressTracker
from enum import Enum
import logger


class ProgressType(Enum):
    CLOUD = 1
    LAZY_CLOUD = 2
    FILE = 3
    LAZY_CLOUD_CACHE = 4
    NONE = 5


class Application:
    def run(self):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Backup')
        parser.add_argument('command', help='''
            Subcommand to run

            The following subcommands are supported:
                statistics
                upload
                download
        ''')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, args.command)()


    def upload(self):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Upload')
        self.__add_remote_directory_argument(parser)
        self.__add_local_directory_argument(parser)
        self.__add_token_argument(parser)
        self.__add_progress_argument(parser)
        self.__add_encryption_password_argument(parser)
        self.__add_skip_argument(parser)
        self.__add_log_file_argument(parser)
        args = self.__parse_sub_command_arguments(parser)
        bearer = get_bearer_token() if args.token is None else args.token
        is_encrypted = args.encryption_pwd is not None
        tracker = self.__get_progress_tracker(args.progress_type, args.progress_file, bearer, args.skip, True)
        builder = self.__get_resource_builder(is_encrypted, args.local_dir, args.mycloud_dir)
        self.__set_log_file(args.log_file)
        uploader = Uploader(bearer, args.local_dir, args.mycloud_dir, tracker, args.encryption_pwd, builder)
        uploader.upload()


    def download(self):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Download')
        self.__add_remote_directory_argument(parser)
        self.__add_local_directory_argument(parser, False)
        self.__add_token_argument(parser)
        self.__add_progress_argument(parser)
        self.__add_encryption_password_argument(parser)
        self.__add_skip_argument(parser)
        self.__add_log_file_argument(parser)
        args = self.__parse_sub_command_arguments(parser)
        tracker = self.__get_progress_tracker(args.progress_type, args.progress_file, bearer, args.skip, False)
        bearer = get_bearer_token() if args.token is None else args.token
        is_encrypted = args.encryption_pwd is not None
        builder = self.__get_resource_builder(is_encrypted, args.local_dir, args.mycloud_dir)
        self.__set_log_file(args.log_file)
        downloader = Downloader(bearer, args.local_dir, args.mycloud_dir, tracker, args.encryption_pwd, builder)
        downloader.download()


    def statistics(self):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Statistics')
        self.__add_remote_directory_argument(parser)
        self.__add_token_argument(parser)
        self.__add_log_file_argument(parser)
        args = self.__parse_sub_command_arguments(parser)


    def __parse_sub_command_arguments(self, argument_parser):
        return argument_parser.parse_args(sys.argv[2:])


    def __add_remote_directory_argument(self, argument_parser):
        command = 'mycloud_dir'
        def is_valid(value):
            Application.__must_be_not_empty_string(value, command)
            if not value.startswith('/Drive/'):
                logger.log(f'{command} must start with /Drive/', True)
                sys.exit(2)
            return value
        argument_parser.add_argument(f'--{command}', metavar='m', type=is_valid, help='Base path in Swisscom myCloud')


    def __add_local_directory_argument(self, argument_parser, directory_should_exist=True):
        command = 'local_dir'
        def is_valid(value):
            Application.__must_be_not_empty_string(value, command)
            if directory_should_exist and not os.path.isdir(value):
                logger.log(f'{command} must be an existing directory', True)
                sys.exit(2)
            return value
        argument_parser.add_argument(f'--{command}', metavar='l', type=is_valid, help='Local directory')


    def __add_token_argument(self, argument_parser):
        command = 'token'
        def is_valid(value):
            Application.__must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='t', type=is_valid, help='Swisscom myCloud bearer token')


    def __add_progress_file_argument(self, argument_parser):
        command = 'progress_file'
        def is_valid(value):
            if value is None:
                return value
            if type(value) is not str:
                return value
            Application.__path_is_in_valid_directory(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='p', type=is_valid, help='Path to the progress file') 


    def __add_progress_argument(self, argument_parser):
        command = 'progress_type'
        valid_types = [
            'CLOUD',
            'LAZY_CLOUD',
            'FILE',
            'LAZY_CLOUD_CACHE',
            'NONE'
        ]
        def is_valid(value):
            value = value.upper() if type(value) is str else ''
            if value not in valid_types:
                concatenated = ', '.join(valid_types)
                logger.log(f'{command} must be one of {concatenated}', True)
                sys.exit(2)
            if value == valid_types[0]:
                return ProgressType.CLOUD 
            elif value == valid_types[1]:
                return ProgressType.LAZY_CLOUD 
            elif value == valid_types[2]:
                return ProgressType.FILE
            elif value == valid_types[3]:
                return ProgressType.LAZY_CLOUD_CACHE
            elif value == valid_types[4]:
                return ProgressType.NONE
            else:
                return ProgressType.NONE
        argument_parser.add_argument(f'--{command}', metavar='p', type=is_valid, help='''
            Progress type to be used to measure progress of the current action.
            
            Valid types are:
                CLOUD: Use files in cloud
                LAZY_CLOUD: Use files in cloud lazily
                FILE: Use local file (progress_file parameter required)
                LAZY_CLOUD_CACHE: Use local files or lazy cloud (requires progress_file prameter)
                NONE: no progress (DEFAULT)
        ''')
        self.__add_progress_file_argument(argument_parser)


    def __add_encryption_password_argument(self, argument_parser):
        command = 'encryption_pwd'
        def is_valid(value):
            if value is None:
                return value
            Application.__min_length(value, command, min_length=4)
            return value
        argument_parser.add_argument(f'--{command}', metavar='w', type=is_valid, help='Password used for encryption')


    def __add_skip_argument(self, argument_parser):
        command = 'skip'
        argument_parser.add_argument(f'--{command}', metavar='s', help='Paths to skip', nargs='+')


    def __add_log_file_argument(self, argument_parser):
        command = 'log_file'
        def is_valid(value):
            if value is None:
                return value
            if type(value) is not str:
                return value
            Application.__must_be_not_empty_string(value, command)
            Application.__path_is_in_valid_directory(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='g', help='Path to log file', type=is_valid)


    def __get_progress_tracker(self, progress_type, progress_file, bearer, skip_paths, upload):
        tracker = None
        if progress_type == ProgressType.NONE or progress_type is None:
            tracker = NoProgressTracker()
        elif progress_type == ProgressType.CLOUD and upload:
            tracker = CloudProgressTracker(bearer, mycloud_dir)
        elif progress_type == ProgressType.LAZY_CLOUD and upload:
            tracker = LazyCloudProgressTracker(bearer)
        elif progress_type == ProgressType.FILE:
            tracker = FileProgressTracker(progress_file)
        elif progress_type == ProgressType.LAZY_CLOUD_CACHE and upload:
            tracker = LazyCloudCacheProgressTracker(bearer, progress_file)
        else:
            tracker = NoProgressTracker()
        tracker.load_if_exists()
        if skip_paths is not None:
            skipped = ', '.join(skip_paths)
            logger.log(f'Skipping files: {skipped}')
            tracker.set_skipped_paths(skip_paths)
        return tracker


    def __get_resource_builder(self, is_encrypted, local_dir, mycloud_dir) -> ObjectResourceBuilder:
        with open('./replacements.json', 'r') as f:
            replacement_table = json.load(f)
        builder = ObjectResourceBuilder(local_dir, mycloud_dir, is_encrypted, replacement_table)
        return builder


    def __set_log_file(self, log_file):
        if log_file is not None:
            logger.LOG_FILE = log_file


    @staticmethod
    def __must_be_not_empty_string(value, command):
        Application.__must_be_string(value, command)
        if value == '':
            logger.log(f'{command} must not be empty', True)
            sys.exit(2)


    @staticmethod
    def __must_be_string(value, command):
        if type(value) is not str:
            logger.log(f'{command} must be a string', True)
            sys.exit(2)


    @staticmethod
    def __min_length(value, command, min_length):
        Application.__must_be_string()
        if min_length > 0:
            Application.__must_be_not_empty_string(value, command)
            if len(value) <= min_length:
                logger.log(f'{command} must be at least {min_length} characters long', True)
                sys.exit(2)


    @staticmethod
    def __path_is_in_valid_directory(value, command):
        dir = os.path.basename(value)
        if not os.path.isdir(dir):
            logger.log(f'{command} must be in a valid directory', True)
            sys.exit(2)


if __name__ == '__main__':
    Application().run()