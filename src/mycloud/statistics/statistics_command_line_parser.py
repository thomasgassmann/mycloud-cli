import argparse
from logger import log
from statistics.summarizer import summarize


class StatisticsCommandLineParser:
    def __init__(self, app):
        self.app = app


    def parse_and_execute(self, args):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Statistics', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(f'command', help='''
            All statistics command:
                summary
        ''')
        parsed = parser.parse_args(args[:1])
        if not hasattr(self, parsed.command):
            log('Unrecognized command', True)
            print()
            parser.print_help()
            exit(1)
        getattr(self, parsed.command)(args[1:])


    def summary(self, args):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Statistics', formatter_class=argparse.RawTextHelpFormatter)
        self.app._add_remote_directory_argument(parser)
        self.app._add_token_argument(parser)
        self.app._add_log_file_argument(parser)
        self.app._add_user_name_password(parser)
        args = parser.parse_args(args)
        executor = self.app._get_request_executor(args)
        self.app._set_log_file(args.log_file)
        summarize(executor, args.mycloud_dir)


    def changes(self, args):
        parser = argparse.ArgumentParser(description='Swisscom myCloud Change Detection', formatter_class=argparse.RawTextHelpFormatter)
        self.app._add_remote_directory_argument(parser)
        self.app._add_token_argument(parser)
        self.app._add_log_file_argument(parser)
        self.app._add_user_name_password(parser)
        parser.add_argument('--top', help='Amount of changes to list', type=int, required=True)
        args = parser.parse_args(args)
        executor = self.app._get_request_executor(args)
        self.app._set_log_file(args.log_file)
        print(args)