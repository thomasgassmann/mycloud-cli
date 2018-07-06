import argparse, os, sys, json
from upload import Uploader
from download import Downloader
from statistics import StatisticsCommandLineParser
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
        parser = argparse.ArgumentParser(description='Swisscom myCloud Backup', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('command', help='''
            Subcommand to run

            The following subcommands are supported:
                statistics
                upload
                download
        ''')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command) or args.command == self.run.__name__:
            logger.log('Unrecognized command', True)
            print()
            parser.print_help()
            exit(1)
        getattr(self, args.command)()


    def upload(self):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Upload', formatter_class=argparse.RawTextHelpFormatter)
        self.__add_remote_directory_argument(parser)
        self.__add_local_directory_argument(parser)
        self.__add_token_argument(parser)
        self.__add_progress_argument(parser, True)
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
        parser = argparse.ArgumentParser(description='Swisscom myCloud Download', formatter_class=argparse.RawTextHelpFormatter)
        self.__add_remote_directory_argument(parser)
        self.__add_local_directory_argument(parser, False)
        self.__add_token_argument(parser)
        self.__add_progress_argument(parser, False)
        self.__add_encryption_password_argument(parser)
        self.__add_skip_argument(parser)
        self.__add_log_file_argument(parser)
        args = self.__parse_sub_command_arguments(parser)
        bearer = get_bearer_token() if args.token is None else args.token
        tracker = self.__get_progress_tracker(args.progress_type, args.progress_file, bearer, args.skip, False)
        is_encrypted = args.encryption_pwd is not None
        builder = self.__get_resource_builder(is_encrypted, args.local_dir, args.mycloud_dir)
        self.__set_log_file(args.log_file)
        downloader = Downloader(bearer, args.local_dir, args.mycloud_dir, tracker, args.encryption_pwd, builder)
        downloader.download()


    def statistics(self):
        pass
        # command_line_parser = StatisticsCommandLineParser()
        # command_line_parser.parse_and_execute(sys.argv[3:])        


    def __parse_sub_command_arguments(self, argument_parser):
        return argument_parser.parse_args(sys.argv[2:])


    def __add_remote_directory_argument(self, argument_parser):
        command = 'mycloud_dir'
        def is_valid(value):
            Application.__must_be_not_empty_string(value, command)
            if not value.startswith('/Drive/'):
                raise argparse.ArgumentTypeError(f'{command} must start with /Drive/', True)
                sys.exit(2)
            return value
        argument_parser.add_argument(f'--{command}', metavar='m', type=is_valid, help='Base path in Swisscom myCloud', required=True)


    def __add_local_directory_argument(self, argument_parser, directory_should_exist=True):
        command = 'local_dir'
        def is_valid(value):
            Application.__must_be_not_empty_string(value, command)
            if directory_should_exist and not os.path.isdir(value):
                raise argparse.ArgumentTypeError(f'{command} must be an existing directory', True)
                sys.exit(2)
            return value
        argument_parser.add_argument(f'--{command}', metavar='l', type=is_valid, help='Local directory', required=True)


    def __add_token_argument(self, argument_parser):
        command = 'token'
        def is_valid(value):
            Application.__must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='t', type=is_valid, help='Swisscom myCloud bearer token', required=False)


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


    def __add_progress_argument(self, argument_parser, upload):
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
                raise argparse.ArgumentTypeError(f'{command} must be one of {concatenated}', True)
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
        upload_types = '''
                CLOUD: Use files in cloud to measure progress. This will create an initial representation of the files on myCloud.
                LAZY_CLOUD: Use files in cloud to measure progress lazily.
                LAZY_CLOUD_CACHE: Use local file or lazy cloud, if file is not in local file. (requires progress_file prameter)
        '''
        description_help = '''
            Progress type to be used to measure progress of the current action.
            
            Valid types are:
                FILE: Use local JSON file. (progress_file parameter required)
                NONE: No progress measurement. (DEFAULT)
        '''.strip()
        if upload:
            description_help += upload_types
        argument_parser.add_argument(f'--{command}', metavar='p', type=is_valid, help=description_help)
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
        def default_if_no_upload(tried_tracker):
            if not upload:
                logger.log(f'{str(tried_tracker)} progress tracker not available for download. Defaulting to NoProgressTracker', True)
                tracker = NoProgressTracker()

        tracker = None
        if progress_type == ProgressType.NONE or progress_type is None:
            tracker = NoProgressTracker()
        elif progress_type == ProgressType.CLOUD:
            tracker = CloudProgressTracker(bearer, mycloud_dir)
            default_if_no_upload(ProgressType.CLOUD)
        elif progress_type == ProgressType.LAZY_CLOUD:
            tracker = LazyCloudProgressTracker(bearer)
            default_if_no_upload(ProgressType.LAZY_CLOUD)
        elif progress_type == ProgressType.FILE:
            tracker = FileProgressTracker(progress_file)
        elif progress_type == ProgressType.LAZY_CLOUD_CACHE:
            tracker = LazyCloudCacheProgressTracker(bearer, progress_file)
            default_if_no_upload(ProgressType.LAZY_CLOUD_CACHE)
        else:
            tracker = NoProgressTracker()
        tracker.load_if_exists()
        if skip_paths is not None:
            skipped = ', '.join(skip_paths)
            logger.log(f'Skipping files: {skipped}')
            tracker.set_skipped_paths(skip_paths)
        logger.log(f'Using progress tracker {type(tracker).__name__}')
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
            raise argparse.ArgumentTypeError(f'{command} must not be empty', True)
            sys.exit(2)


    @staticmethod
    def __must_be_string(value, command):
        if type(value) is not str:
            raise argparse.ArgumentTypeError(f'{command} must be a string', True)
            sys.exit(2)


    @staticmethod
    def __min_length(value, command, min_length):
        Application.__must_be_string(value, command)
        if min_length > 0:
            Application.__must_be_not_empty_string(value, command)
            if len(value) <= min_length:
                raise argparse.ArgumentTypeError(f'{command} must be at least {min_length} characters long', True)
                sys.exit(2)


    @staticmethod
    def __path_is_in_valid_directory(value, command):
        dir = os.path.dirname(value)
        if not os.path.isdir(dir):
            raise argparse.ArgumentTypeError(f'{command} must be in a valid directory', True)
            sys.exit(2)


if __name__ == '__main__':
    Application().run()