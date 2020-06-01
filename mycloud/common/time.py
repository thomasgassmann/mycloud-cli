from datetime import datetime


def parse_datetime(input_str: str) -> datetime:
    if '.' not in input_str:
        return datetime.strptime(input_str, '%Y-%m-%dT%H:%M:%SZ')
    return datetime.strptime(input_str, '%Y-%m-%dT%H:%M:%S.%fZ')
