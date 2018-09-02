import os
import datetime
import json
import threading
from collections import defaultdict
from colorama import Fore, Style, init
from mycloud.constants import REQUEST_STATISTICS_LOCATION, REQUEST_COUNT_IDENTIFIER


init()


LOG_FILE = ''


if os.path.isfile(REQUEST_STATISTICS_LOCATION):
    with open(REQUEST_STATISTICS_LOCATION, 'r') as f:
        statistics = json.load(f)
else:
    statistics = {}


def add_request_count(request_identifier):
    if REQUEST_COUNT_IDENTIFIER not in statistics:
        statistics[REQUEST_COUNT_IDENTIFIER] = {}
    if request_identifier not in statistics[REQUEST_COUNT_IDENTIFIER]:
        statistics[REQUEST_COUNT_IDENTIFIER][request_identifier] = 0
    statistics[REQUEST_COUNT_IDENTIFIER][request_identifier] += 1


def save_files():
    # TODO: also save log file
    dir = os.path.dirname(REQUEST_STATISTICS_LOCATION)
    if not os.path.isdir(dir):
        os.makedirs(dir)
    with open(REQUEST_STATISTICS_LOCATION, 'w') as f:
        json.dump(statistics, f)


def log(string: str, error=False, end='\n'):
    if error:
        string = 'ERR: {}'.format(string)
    formatted_time = datetime.datetime.now().strftime('%H:%M:%S')
    thread_id = threading.get_ident()
    string = '({}) {}: {}'.format(thread_id, formatted_time, string)
    color = Fore.RED if error else Fore.WHITE
    print('{}{}{}'.format(color, string, Style.RESET_ALL), end=end)
    if LOG_FILE == '':
        return
    try:
        with open(LOG_FILE, 'a', encoding='utf8') as file:
            file.write(string)
            file.write('\n')
    except Exception as ex:
        print('ERR: Failed to write to log file: {}'.format(str(ex)))
