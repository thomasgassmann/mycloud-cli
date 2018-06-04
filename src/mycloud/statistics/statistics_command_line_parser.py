import argparse
from backup import Application


class StatisticsCommandLineParser:
    def __init__(self, application: Application):
        self.application = application


    def parse_and_execute(self, args):


        parser = argparse.ArgumentParser(description='Swisscom myCloud Statistics', formatter_class=argparse.RawTextHelpFormatter)
        self.__add_remote_directory_argument(parser)
        self.__add_token_argument(parser)
        self.__add_log_file_argument(parser)
        args = self.__parse_sub_command_arguments(parser)
        self.__set_log_file(args.log_file)
        bearer = get_bearer_token() if args.token is None else args.token



        parser = argparse.ArgumentParser(description='Swisscom myCloud Statistics', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(f'command', help='''
            All statistics command:
                summary
        ''', required=True)
        args = parser.parse_args(args[:1])
        if not hasattr(self, args.command):
            logger.log('Unrecognized command', True)
            print()
            parser.print_help()
            exit(1)
        getattr(self, args.command)(args[1:])


    def summary(self, args):
        pass