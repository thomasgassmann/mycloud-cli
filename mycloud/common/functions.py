import os
import tempfile


def get_string_generator(string: str):
    handle, filename = tempfile.mkstemp()
    with os.fdopen(handle, 'w') as file_stream:
        file_stream.write(string)
    with open(filename, 'rb') as file_stream:
        yield file_stream.read()
