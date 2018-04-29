from mycloudapi import ObjectResourceBuilder
from progress import ProgressTracker
from encryption import Encryptor


ENCRYPTION_CHUNK_LENGTH = 1024


class SyncBase:
    def __init__(self, bearer: str, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, encryption_password: str):
        self.bearer_token = bearer
        self.local_directory = local_directory
        self.mycloud_directory = mycloud_directory
        self.progress_tracker = tracker
        self.is_encrypted = encryption_password is not None
        self.encryption_password = encryption_password
        self.builder = ObjectResourceBuilder(self.local_directory, self.mycloud_directory, self.is_encrypted)
        self.encryptor = Encryptor(encryption_password, ENCRYPTION_CHUNK_LENGTH) if self.is_encrypted else None


    def update_encryptor(self):
        if self.is_encrypted:
            self.encryptor = Encryptor(self.encryption_password, ENCRYPTION_CHUNK_LENGTH) if self.is_encrypted else None