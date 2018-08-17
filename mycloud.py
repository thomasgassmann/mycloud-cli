import argparse
import traceback
import os
import sys
import json
from enum import Enum
import mycloud.logger as logger
from mycloud.filesync import upsync_folder, downsync_folder, convert_remote_files
from mycloud.filesystem import BasicRemotePath
from mycloud.statistics import StatisticsCommandLineParser
from mycloud.mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from mycloud.mycloudapi.auth import MyCloudAuthenticator
from mycloud.proxy import run_server
from mycloud.filesync.progress import ProgressTracker


class Application:
    def run(self):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Backup', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('command', help='''
            Subcommand to run

            The following subcommands are supported:
                statistics
                upload
                download
                shell
                convert (Deprecated)
        ''')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command) or args.command == self.run.__name__:
            logger.log('Unrecognized command', True)
            print()
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    def shell(self):
        # TODO: implement shell
        input('> ')
        pass

    def upload(self):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Upload', formatter_class=argparse.RawTextHelpFormatter)
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser)
        self._add_token_argument(parser)
        self._add_encryption_password_argument(parser)
        self._add_skip_argument(parser)
        self._add_log_file_argument(parser)
        self._add_user_name_password(parser)
        args = self._parse_sub_command_arguments(parser)
        executor = self._get_request_executor(args)
        tracker = self._get_progress_tracker(args.skip)
        builder = self._get_resource_builder(args.local_dir, args.mycloud_dir)
        self._set_log_file(args.log_file)
        upsync_folder(executor, builder, args.local_dir,
                      tracker, args.encryption_pwd)

    def download(self):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Download', formatter_class=argparse.RawTextHelpFormatter)
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser, False)
        self._add_token_argument(parser)
        self._add_encryption_password_argument(parser)
        self._add_skip_argument(parser)
        self._add_log_file_argument(parser)
        self._add_user_name_password(parser)
        args = self._parse_sub_command_arguments(parser)
        executor = self._get_request_executor(args)
        tracker = self._get_progress_tracker(args.skip)
        builder = self._get_resource_builder(args.local_dir, args.mycloud_dir)
        self._set_log_file(args.log_file)
        translatable_path = BasicRemotePath(args.mycloud_dir)
        downsync_folder(executor, builder, translatable_path,
                        tracker, args.encryption_pwd)

    def convert(self):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Remote File Converter', formatter_class=argparse.RawTextHelpFormatter)
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser)
        self._add_user_name_password(parser)
        self._add_token_argument(parser)
        self._add_skip_argument(parser)
        args = self._parse_sub_command_arguments(parser)
        executor = self._get_request_executor(args)
        convert_remote_files(executor, args.mycloud_dir, args.local_dir, args.skip or [])

    def statistics(self):
        command_line_parser = StatisticsCommandLineParser(self)
        command_line_parser.parse_and_execute(sys.argv[2:])

    def proxy(self):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Proxy', formatter_class=argparse.RawTextHelpFormatter)
        self._add_user_name_password(parser)
        self._add_token_argument(parser)
        self._add_log_file_argument(parser)
        self._add_remote_directory_argument(parser)

        parser.add_argument('--port', metavar='p', type=int,
                            help='The port of the proxy', required=False, default=9001)

        args = self._parse_sub_command_arguments(parser)
        self._set_log_file(args.log_file)
        request_executor = self._get_request_executor(args)

        run_server(request_executor, args.mycloud_dir, args.port)

    def _parse_sub_command_arguments(self, argument_parser):
        return argument_parser.parse_args(sys.argv[2:])

    def _get_request_executor(self, args):
        if args.token is not None and (args.username is not None or args.password is not None):
            raise argparse.ArgumentTypeError(
                'Cannot have a token and username/password authentiation at the same time', True)
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
                raise argparse.ArgumentTypeError(
                    '{} must start with /Drive/'.format(command), True)
                sys.exit(2)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='m', type=is_valid, help='Base path in Swisscom myCloud', required=True)

    def _add_local_directory_argument(self, argument_parser, directory_should_exist=True):
        command = 'local_dir'

        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            if directory_should_exist and not os.path.isdir(value) and not value.endswith(os.sep):
                raise argparse.ArgumentTypeError(
                    '{} must be an existing directory'.format(command), True)
                sys.exit(2)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='l', type=is_valid, help='Local directory', required=True)

    def _add_token_argument(self, argument_parser):
        command = 'token'

        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='t', type=is_valid, help='Swisscom myCloud bearer token', required=False)

    def _add_user_name_password(self, argument_parser):
        command = 'username'

        def is_valid_username(value):
            Application._must_be_not_empty_string(value, command)
            if '@' not in value:
                raise argparse.ArgumentTypeError(
                    '{} must be an email address'.format(command), True)
                sys.exit(2)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='u', type=is_valid_username, help='Email of the user for myCloud', required=False)

        command = 'password'

        def is_valid_password(value):
            Application._must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='p', type=is_valid_password, help='Password for the myCloud user', required=False)

    def _add_progress_file_argument(self, argument_parser):
        command = 'progress_file'

        def is_valid(value):
            if value is None:
                return value
            if type(value) is not str:
                return value
            Application._path_is_in_valid_directory(value, command)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='p', type=is_valid, help='Path to the progress file')

    def _add_encryption_password_argument(self, argument_parser):
        command = 'encryption_pwd'

        def is_valid(value):
            if value is None:
                return value
            Application._min_length(value, command, min_length=4)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='w', type=is_valid, help='Password used for encryption')

    def _add_skip_argument(self, argument_parser):
        command = 'skip'
        argument_parser.add_argument(
            '--{}'.format(command), metavar='s', help='Paths to skip', nargs='+')

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
        argument_parser.add_argument(
            '--{}'.format(command), metavar='g', help='Path to log file', type=is_valid)

    def _get_progress_tracker(self, skip_paths):
        tracker = ProgressTracker()
        if skip_paths is not None:
            skipped = ', '.join(skip_paths)
            logger.log('Skipping files: {}'.format(skipped))
            tracker.set_skipped_paths(skip_paths)
        return tracker

    def _get_resource_builder(self, local_dir, mycloud_dir):
        builder = ObjectResourceBuilder(local_dir, mycloud_dir)
        return builder

    def _set_log_file(self, log_file):
        if log_file is not None:
            logger.LOG_FILE = log_file

    @staticmethod
    def _must_be_not_empty_string(value, command):
        Application._must_be_string(value, command)
        if value == '':
            raise argparse.ArgumentTypeError(
                '{} must not be empty'.format(command), True)
            sys.exit(2)

    @staticmethod
    def _must_be_string(value, command):
        if type(value) is not str:
            raise argparse.ArgumentTypeError(
                '{} must be a string'.format(command), True)
            sys.exit(2)

    @staticmethod
    def _min_length(value, command, min_length):
        Application._must_be_string(value, command)
        if min_length > 0:
            Application._must_be_not_empty_string(value, command)
            if len(value) <= min_length:
                raise argparse.ArgumentTypeError(
                    '{} must be at least {} characters long'.format(command, min_length), True)
                sys.exit(2)

    @staticmethod
    def _path_is_in_valid_directory(value, command):
        dir = os.path.dirname(value)
        if not os.path.isdir(dir):
            raise argparse.ArgumentTypeError(
                '{} must be in a valid directory'.format(command), True)
            sys.exit(2)


if __name__ == '__main__':
    try:
        Application().run()
    except Exception as ex:
        logger.log('FATAL: {}'.format(str(ex)), error=True)
        traceback.print_exc()