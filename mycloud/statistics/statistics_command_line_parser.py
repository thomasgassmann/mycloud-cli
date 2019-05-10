import argparse
from mycloud.logger import log
from mycloud.statistics.size import calculate_size


class StatisticsCommandLineParser:
    def __init__(self, app):
        self.app = app

    def parse_and_execute(self, args):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Statistics',
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('command', help='''
            All statistics command:
                summary
                changes
                usage
                size
        ''')
        parsed = parser.parse_args(args[:1])
        if not hasattr(self, parsed.command):
            log('Unrecognized command', True)
            print()
            parser.print_help()
            exit(1)
        getattr(self, parsed.command)(args[1:])

    def size(self, args):
        parser = argparse.ArgumentParser(
            description='Swisscom myCloud Size Calculation', formatter_class=argparse.RawTextHelpFormatter)
        self.app._add_remote_directory_argument(parser)
        self.app._add_token_argument(parser)
        self.app._add_log_file_argument(parser)
        self.app._add_user_name_password(parser)
        args = parser.parse_args(args)
        executor = self.app._get_request_executor(args)
        self.app._set_log_file(args.log_file)
        calculate_size(executor, args.mycloud_dir)
