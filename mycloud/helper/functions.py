import os
import tempfile


def get_string_generator(string: str):
    fd, filename = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as f:
        f.write(string)
    with open(filename, 'rb') as f:
        yield f.read()
