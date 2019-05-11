import os
import datetime
import json
import threading
from colorama import Fore, Style, init
from mycloud.constants import REQUEST_STATISTICS_LOCATION, REQUEST_COUNT_IDENTIFIER


init()


LOG_FILE = ''
LOGS = []


if os.path.isfile(REQUEST_STATISTICS_LOCATION):
    with open(REQUEST_STATISTICS_LOCATION, 'r') as f:
        STATISTICS = json.load(f)
else:
    STATISTICS = {}


def add_request_count(request_identifier):
    if REQUEST_COUNT_IDENTIFIER not in STATISTICS:
        STATISTICS[REQUEST_COUNT_IDENTIFIER] = {}
    if request_identifier not in STATISTICS[REQUEST_COUNT_IDENTIFIER]:
        STATISTICS[REQUEST_COUNT_IDENTIFIER][request_identifier] = 0
    STATISTICS[REQUEST_COUNT_IDENTIFIER][request_identifier] += 1


def save_files():
    directory = os.path.dirname(REQUEST_STATISTICS_LOCATION)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    # TODO: use operation_timeout
    file_stream = open(REQUEST_STATISTICS_LOCATION, 'w')
    json.dump(STATISTICS, file_stream)
    f.close()
    if LOG_FILE == '':
        return
    global LOGS
    try:
        with open(LOG_FILE, 'a', encoding='utf8') as file_stream:
            for string in LOGS:
                file_stream.write(string)
                file_stream.write('\n')
            LOGS[:] = []
    except Exception as ex:
        print('ERR: Failed to write to log file: {}'.format(str(ex)))


def log(string: str, error=False, end='\n'):
    global LOGS
    if error:
        string = 'ERR: {}'.format(string)
    formatted_time = datetime.datetime.now().strftime('%H:%M:%S')
    thread_id = threading.get_ident()
    string = '({}) {}: {}'.format(thread_id, formatted_time, string)
    color = Fore.RED if error else Fore.WHITE
    print('{}{}{}'.format(color, string, Style.RESET_ALL), end=end)
    LOGS.append(string)
