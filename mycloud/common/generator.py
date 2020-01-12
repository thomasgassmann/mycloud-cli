import logging
from mycloud.constants import CHUNK_SIZE


def to_generator(readable):
    def generator():
        total_read = 0
        print_every = 1000
        read_size = CHUNK_SIZE
        while True:
            chunk = readable.read(read_size)
            if not chunk:
                break

            total_read += len(chunk)
            if total_read / read_size % print_every == 0:
                logging.debug(f'Read total: {total_read}')

            yield chunk

    return generator()
