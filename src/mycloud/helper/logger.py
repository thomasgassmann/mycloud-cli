import os
from constants import LOG_FILE


def log(str: str):
    print(str)
    with open(LOG_FILE, 'a') as file:
        file.write(str)