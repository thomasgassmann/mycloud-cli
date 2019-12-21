import base64
import io


def get_object_id(string: str):
    base_64 = base64.b64encode(string.encode())
    return str(base_64, 'utf-8')


def raise_if_invalid_drive_path(path: str):
    if not path.startswith('/Drive/'):
        raise ValueError('Object path for myCloud must start with /Drive')


def generator_to_stream(generator, buffer_size=io.DEFAULT_BUFFER_SIZE):
    class GeneratorStream(io.RawIOBase):
        def __init__(self):
            self._leftover = None

        def readable(self):
            return True

        def readinto(self, b):
            try:
                l = len(b)
                chunk = self._leftover or next(generator)
                output, self._leftover = chunk[:l], chunk[l:]
                b[:len(output)] = output
                return len(output)
            except StopIteration:
                return 0
    return io.BufferedReader(GeneratorStream())
