import argparse, os, sys, json
from upload import Uploader
from download import Downloader
from statistics import StatisticsCommandLineParser
from mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from mycloudapi.auth import MyCloudAuthenticator
from proxy import ProxyServer
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
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser)
        self._add_token_argument(parser)
        self._add_progress_argument(parser, True)
        self._add_encryption_password_argument(parser)
        self._add_skip_argument(parser)
        self._add_log_file_argument(parser)
        self._add_user_name_password(parser)
        args = self._parse_sub_command_arguments(parser)
        executor = self._get_request_executor(args)
        is_encrypted = args.encryption_pwd is not None
        tracker = self._get_progress_tracker(args.progress_type, args.progress_file, executor, args.skip, True)
        builder = self._get_resource_builder(is_encrypted, args.local_dir, args.mycloud_dir)
        self._set_log_file(args.log_file)
        uploader = Uploader(executor, args.local_dir, args.mycloud_dir, tracker, args.encryption_pwd, builder)
        uploader.upload()


    def download(self):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Download', formatter_class=argparse.RawTextHelpFormatter)
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser, False)
        self._add_token_argument(parser)
        self._add_progress_argument(parser, False)
        self._add_encryption_password_argument(parser)
        self._add_skip_argument(parser)
        self._add_log_file_argument(parser)
        self._add_user_name_password(parser)
        args = self._parse_sub_command_arguments(parser)
        executor = self._get_request_executor(args)
        tracker = self._get_progress_tracker(args.progress_type, args.progress_file, executor, args.skip, False)
        is_encrypted = args.encryption_pwd is not None
        builder = self._get_resource_builder(is_encrypted, args.local_dir, args.mycloud_dir)
        self._set_log_file(args.log_file)
        downloader = Downloader(executor, args.local_dir, args.mycloud_dir, tracker, args.encryption_pwd, builder)
        downloader.download()


    def statistics(self):
        pass
        # command_line_parser = StatisticsCommandLineParser()
        # command_line_parser.parse_and_execute(sys.argv[3:])        


    def proxy(self):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Proxy', formatter_class=argparse.RawTextHelpFormatter)
        self._add_user_name_password(parser)
        self._add_token_argument(parser)
        self._add_log_file_argument(parser)
        self._add_remote_directory_argument(parser)

        self._set_log_file(args.log_file)

        args = self._parse_sub_command_arguments(parser)
        request_executor = self._get_request_executor(args)

        proxy = ProxyServer(request_executor, args.mycloud_dir)
        proxy.run_server()


    def _parse_sub_command_arguments(self, argument_parser):
        return argument_parser.parse_args(sys.argv[2:])


    def _get_request_executor(self, args):
        if args.token is not None and (args.username is not None or args.password is not None):
            raise argparse.ArgumentTypeError('Cannot have a token and username/password authentiation at the same time', True)
        auth = MyCloudAuthenticator()
        if args.token:
            auth.set_bearer_auth(args.token)
        elif args.username and args.password:
            auth.set_password_auth(args.username, args.password)
        request_executor = MyCloudRequestExecutor(auth)
        return request_executor


    def _add_remote_directory_argument(self, argument_parser):
        command = 'mycloud_dir'
        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            if not value.startswith('/Drive/'):
                raise argparse.ArgumentTypeError(f'{command} must start with /Drive/', True)
                sys.exit(2)
            return value
        argument_parser.add_argument(f'--{command}', metavar='m', type=is_valid, help='Base path in Swisscom myCloud', required=True)


    def _add_local_directory_argument(self, argument_parser, directory_should_exist=True):
        command = 'local_dir'
        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            if directory_should_exist and not os.path.isdir(value) and not value.endswith(os.sep):
                raise argparse.ArgumentTypeError(f'{command} must be an existing directory', True)
                sys.exit(2)
            return value
        argument_parser.add_argument(f'--{command}', metavar='l', type=is_valid, help='Local directory', required=True)


    def _add_token_argument(self, argument_parser):
        command = 'token'
        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='t', type=is_valid, help='Swisscom myCloud bearer token', required=False)

    
    def _add_user_name_password(self, argument_parser):
        command = 'username'
        def is_valid_username(value):
            Application._must_be_not_empty_string(value, command)
            if '@' not in value:
                raise argparse.ArgumentTypeError(f'{command} must be an email address', True)
                sys.exit(2)
            return value
        argument_parser.add_argument(f'--{command}', metavar='u', type=is_valid_username, help='Email of the user for myCloud', required=False)

        command = 'password'
        def is_valid_password(value):
            Application._must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='p', type=is_valid_password, help='Password for the myCloud user', required=False)


    def _add_progress_file_argument(self, argument_parser):
        command = 'progress_file'
        def is_valid(value):
            if value is None:
                return value
            if type(value) is not str:
                return value
            Application._path_is_in_valid_directory(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='p', type=is_valid, help='Path to the progress file') 


    def _add_progress_argument(self, argument_parser, upload):
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
        self._add_progress_file_argument(argument_parser)


    def _add_encryption_password_argument(self, argument_parser):
        command = 'encryption_pwd'
        def is_valid(value):
            if value is None:
                return value
            Application._min_length(value, command, min_length=4)
            return value
        argument_parser.add_argument(f'--{command}', metavar='w', type=is_valid, help='Password used for encryption')


    def _add_skip_argument(self, argument_parser):
        command = 'skip'
        argument_parser.add_argument(f'--{command}', metavar='s', help='Paths to skip', nargs='+')


    def _add_log_file_argument(self, argument_parser):
        command = 'log_file'
        def is_valid(value):
            if value is None:
                return value
            if type(value) is not str:
                return value
            Application._must_be_not_empty_string(value, command)
            Application._path_is_in_valid_directory(value, command)
            return value
        argument_parser.add_argument(f'--{command}', metavar='g', help='Path to log file', type=is_valid)


    def _get_progress_tracker(self, progress_type, progress_file, executor, skip_paths, upload):
        def default_if_no_upload(tried_tracker):
            if not upload:
                logger.log(f'{str(tried_tracker)} progress tracker not available for download. Defaulting to NoProgressTracker', True)
                tracker = NoProgressTracker()

        tracker = None
        if progress_type == ProgressType.NONE or progress_type is None:
            tracker = NoProgressTracker()
        elif progress_type == ProgressType.CLOUD:
            tracker = CloudProgressTracker(executor, mycloud_dir)
            default_if_no_upload(ProgressType.CLOUD)
        elif progress_type == ProgressType.LAZY_CLOUD:
            tracker = LazyCloudProgressTracker(executor)
            default_if_no_upload(ProgressType.LAZY_CLOUD)
        elif progress_type == ProgressType.FILE:
            tracker = FileProgressTracker(progress_file)
        elif progress_type == ProgressType.LAZY_CLOUD_CACHE:
            tracker = LazyCloudCacheProgressTracker(executor, progress_file)
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


    def _get_resource_builder(self, is_encrypted, local_dir, mycloud_dir) -> ObjectResourceBuilder:
        with open('./replacements.json', 'r') as f:
            replacement_table = json.load(f)
        builder = ObjectResourceBuilder(local_dir, mycloud_dir, is_encrypted, replacement_table)
        return builder


    def _set_log_file(self, log_file):
        if log_file is not None:
            logger.LOG_FILE = log_file


    @staticmethod
    def _must_be_not_empty_string(value, command):
        Application._must_be_string(value, command)
        if value == '':
            raise argparse.ArgumentTypeError(f'{command} must not be empty', True)
            sys.exit(2)


    @staticmethod
    def _must_be_string(value, command):
        if type(value) is not str:
            raise argparse.ArgumentTypeError(f'{command} must be a string', True)
            sys.exit(2)


    @staticmethod
    def _min_length(value, command, min_length):
        Application._must_be_string(value, command)
        if min_length > 0:
            Application._must_be_not_empty_string(value, command)
            if len(value) <= min_length:
                raise argparse.ArgumentTypeError(f'{command} must be at least {min_length} characters long', True)
                sys.exit(2)


    @staticmethod
    def _path_is_in_valid_directory(value, command):
        dir = os.path.dirname(value)
        if not os.path.isdir(dir):
            raise argparse.ArgumentTypeError(f'{command} must be in a valid directory', True)
            sys.exit(2)


if __name__ == '__main__':
    try:
        Application().run()
    except Exception as ex:
        logger.log(f'FATAL: {str(ex)}', error=True)