import os, datetime
from colorama import Fore, Style, init


init()


LOG_FILE = ''


def log(str: str, error=False):
    if error:
        str = f'ERR: {str}'
    formatted_time = datetime.datetime.now().strftime('%H:%M:%S')
    str = f'{formatted_time}: {str}'
    color = Fore.RED if error else Fore.WHITE
    print(f'{color}{str}{Style.RESET_ALL}')
    if LOG_FILE == '':
        return
    try:
        with open(LOG_FILE, 'a', encoding='utf8') as file:
            file.write(str)
            file.write('\n')
    except Exception as ex:
        print(f'ERR: Failed to write to log file: {str(ex)}')