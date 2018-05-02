import os


LOG_FILE = ''


def log(str: str):
    print(str)
    if LOG_FILE == '':
        return
    try:
        with open(LOG_FILE, 'a', encoding='utf8') as file:
            file.write(str)
            file.write('\n')
    except Exception as ex:
        print(f'ERR: Failed to write to log file: {str(ex)}')