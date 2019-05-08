import argparse
import os
import sys
import getpass
import mycloud.logger as logger
from mycloud.credentials.storage import save_validate, get_credentials
from mycloud.mycloudapi.auth.bearer_token import open_for_cert
from mycloud.filesync import upsync_folder, downsync_folder, convert_remote_files
from mycloud.filesystem import BasicRemotePath
from mycloud.statistics import StatisticsCommandLineParser
from mycloud.mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from mycloud.mycloudapi.auth import MyCloudAuthenticator
from mycloud.filesync.progress import ProgressTracker


import click
import pinject
from click.exceptions import ClickException
from mycloud.commands import auth_command, statistics_command


class InstanceBindingSpec(pinject.BindingSpec):
    
    def __init__(self, name, instance):
        self._name = name
        self._instance = instance

    def configure(self, bind):
        bind(self._name, self._instance)


def construct_authenticator(bearer: str):
    authenticator = MyCloudAuthenticator()
    if bearer:
        authenticator.set_bearer_auth(bearer)
    else:
        username, password = get_credentials()
        if not username or not password:
            raise ClickException('Run "mycloud auth login" to authenticate yourself first, or specify a token')
        authenticator.set_password_auth(username, password)


@click.group()
@click.pass_context
@click.option('--token', nargs=1, required=False)
def mycloud_cli(ctx, token):
    if token is not None:
        ctx.obj['token'] = token

    ctx.obj['injector'] = pinject.new_object_graph(binding_specs=[
        InstanceBindingSpec('mycloud_authenticator', construct_authenticator(token))
    ])

mycloud_cli.add_command(auth_command)
mycloud_cli.add_command(statistics_command)


if __name__ == '__main__':
    mycloud_cli(obj={})


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

    def upload(self):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Upload', formatter_class=argparse.RawTextHelpFormatter)
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser)
        self._add_token_argument(parser)
        self._add_encryption_argument(parser)
        self._add_skip_argument(parser)
        self._add_log_file_argument(parser)
        self._add_user_name_password(parser)
        self._add_skip_by_hash(parser)
        args = self._parse_sub_command_arguments(parser)
        executor = self._get_request_executor(args)
        tracker = self._get_progress_tracker(args.skip)
        builder = self._get_resource_builder(args.local_dir, args.mycloud_dir)
        self._set_log_file(args.log_file)
        upsync_folder(executor, builder, args.local_dir,
                      tracker, args.encryption_pwd, not args.skip_by_hash)

    def download(self):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Download', formatter_class=argparse.RawTextHelpFormatter)
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser, False)
        self._add_token_argument(parser)
        self._add_encryption_argument(parser)
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
            description='Swisscom myCloud Remote File Converter',
            formatter_class=argparse.RawTextHelpFormatter)
        self._add_remote_directory_argument(parser)
        self._add_local_directory_argument(parser)
        self._add_user_name_password(parser)
        self._add_token_argument(parser)
        self._add_skip_argument(parser)
        args = self._parse_sub_command_arguments(parser)
        executor = self._get_request_executor(args)
        convert_remote_files(executor, args.mycloud_dir,
                             args.local_dir, args.skip or [])

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

    @staticmethod
    def _parse_sub_command_arguments(argument_parser):
        return argument_parser.parse_args(sys.argv[2:])

    @staticmethod
    def _get_request_executor(args):
        if args.token is not None and (args.username is not None or args.password is not None):
            raise argparse.ArgumentTypeError(
                'Cannot have a token and username/password authentiation at the same time', True)
        auth = MyCloudAuthenticator()
        if args.token:
            auth.set_bearer_auth(args.token)
        elif args.username and args.password:
            auth.set_password_auth(args.username, args.password)
        else:
            (username, password) = get_credentials()
            auth.set_password_auth(username, password)
        request_executor = MyCloudRequestExecutor(auth)
        return request_executor

    @staticmethod
    def _add_remote_directory_argument(argument_parser):
        command = 'mycloud_dir'

        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            if not value.startswith('/Drive/'):
                raise argparse.ArgumentTypeError(
                    '{} must start with /Drive/'.format(command), True)
            return value
        argument_parser.add_argument(
            '--{}'.format(command),
            metavar='m',
            type=is_valid,
            help='Base path in Swisscom myCloud',
            required=True)

    @staticmethod
    def _add_local_directory_argument(argument_parser, directory_should_exist=True):
        command = 'local_dir'

        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            if directory_should_exist and not os.path.isdir(value) and not value.endswith(os.sep):
                raise argparse.ArgumentTypeError(
                    '{} must be an existing directory'.format(command), True)
            return value
        argument_parser.add_argument(
            '--{}'.format(command),
            metavar='l',
            type=is_valid,
            help='Local directory',
            required=True)

    @staticmethod
    def _add_token_argument(argument_parser):
        command = 'token'

        def is_valid(value):
            Application._must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(
            '--{}'.format(command),
            metavar='t',
            type=is_valid,
            help='Swisscom myCloud bearer token',
            required=False)

    @staticmethod
    def _add_user_name_password(argument_parser):
        command = 'username'

        def is_valid_username(value):
            Application._must_be_not_empty_string(value, command)
            if '@' not in value:
                raise argparse.ArgumentTypeError(
                    '{} must be an email address'.format(command), True)
            return value
        argument_parser.add_argument(
            '--{}'.format(command),
            metavar='u',
            type=is_valid_username,
            help='Email of the user for myCloud',
            required=False)

        command = 'password'

        def is_valid_password(value):
            Application._must_be_not_empty_string(value, command)
            return value
        argument_parser.add_argument(
            '--{}'.format(command),
            metavar='p',
            type=is_valid_password,
            help='Password for the myCloud user',
            required=False)

    @staticmethod
    def _add_progress_file_argument(argument_parser):
        command = 'progress_file'

        def is_valid(value):
            if value is None:
                return value
            if not isinstance(value, str):
                return value
            Application._path_is_in_valid_directory(value, command)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='p', type=is_valid, help='Path to the progress file')

    @staticmethod
    def _add_encryption_argument(argument_parser):
        command = 'encryption_pwd'

        def is_valid(value):
            if value is None:
                return value
            Application._min_length(value, command, min_length=4)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='w', type=is_valid, help='Password used for encryption')

    @staticmethod
    def _add_skip_argument(argument_parser):
        command = 'skip'
        argument_parser.add_argument(
            '--{}'.format(command), metavar='s', help='Paths to skip', nargs='+')

    @staticmethod
    def _add_skip_by_hash(argument_parser):
        command = 'skip_by_hash'
        argument_parser.add_argument(
            f'--{command}',
            default=False, action='store_true',
            help='Skip the files to upload by their date and not their hash')

    @staticmethod
    def _add_log_file_argument(argument_parser):
        command = 'log_file'

        def is_valid(value):
            if value is None:
                return value
            if not isinstance(value, str):
                return value
            Application._must_be_not_empty_string(value, command)
            Application._path_is_in_valid_directory(value, command)
            return value
        argument_parser.add_argument(
            '--{}'.format(command), metavar='g', help='Path to log file', type=is_valid)

    @staticmethod
    def _get_progress_tracker(skip_paths):
        tracker = ProgressTracker()
        if skip_paths is not None:
            skipped = ', '.join(skip_paths)
            logger.log('Skipping files: {}'.format(skipped))
            tracker.set_skipped_paths(skip_paths)
        return tracker

    @staticmethod
    def _get_resource_builder(local_dir, mycloud_dir):
        builder = ObjectResourceBuilder(local_dir, mycloud_dir)
        return builder

    @staticmethod
    def _set_log_file(log_file):
        if log_file is not None:
            logger.LOG_FILE = log_file

    @staticmethod
    def _must_be_not_empty_string(value, command):
        Application._must_be_string(value, command)
        if value == '':
            raise argparse.ArgumentTypeError(
                '{} must not be empty'.format(command), True)

    @staticmethod
    def _must_be_string(value, command):
        if not isinstance(value, str):
            raise argparse.ArgumentTypeError(
                '{} must be a string'.format(command), True)

    @staticmethod
    def _min_length(value, command, min_length):
        Application._must_be_string(value, command)
        if min_length > 0:
            Application._must_be_not_empty_string(value, command)
            if len(value) < min_length:
                raise argparse.ArgumentTypeError(
                    '{} must be at least {} characters long'.format(command, min_length), True)

    @staticmethod
    def _path_is_in_valid_directory(value, command):
        directory = os.path.dirname(value)
        if not os.path.isdir(directory):
            raise argparse.ArgumentTypeError(
                '{} must be in a valid directory'.format(command), True)

def main():
    try:
        Application().run()
    except KeyboardInterrupt:
        logger.log('Keyboard Interrupt')
    finally:
        logger.save_files()

if __name__ == '__main__':
    main()
