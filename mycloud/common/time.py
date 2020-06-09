import time
import datetime


def parse_datetime(input_str: str) -> datetime.datetime:
    f = '%Y-%m-%dT%H:%M:%SZ' if '.' not in input_str else '%Y-%m-%dT%H:%M:%S.%fZ'
    return datetime.datetime.strptime(input_str, f)


def to_unix(date: datetime.datetime):
    return time.mktime(date.timetuple())
