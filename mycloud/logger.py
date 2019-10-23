import os
import json
from mycloud.constants import REQUEST_STATISTICS_LOCATION, REQUEST_COUNT_IDENTIFIER


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

    with open(REQUEST_STATISTICS_LOCATION, 'w') as f:
        json.dump(STATISTICS, f)
