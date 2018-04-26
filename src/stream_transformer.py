from encryption import Encryptor
from progress_tracker import ProgressTracker
from io import TextIOWrapper


my_cloud_max_file_size = 3000000000
my_cloud_big_file_chunk_size = 1000000000


class StreamTransformer:
    def __init__(self, encryptor: Encryptor, tracker: ProgressTracker, split_into_chunks=False, chunk_size):
        self.encryptor = encryptor
        self.tracker = tracker


    def upload_generator(self, file_stream: TextIOWrapper):
        def generator():
            pass
        return generator


    def download_generator(self):
        pass