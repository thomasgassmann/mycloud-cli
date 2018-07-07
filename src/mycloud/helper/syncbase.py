from mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor
from progress import ProgressTracker
from encryption import Encryptor
from constants import ENCRYPTION_CHUNK_LENGTH


class SyncBase:
    def __init__(self, request_executor: MyCloudRequestExecutor, local_directory: str, mycloud_directory: str, tracker: ProgressTracker, encryption_password: str, builder: ObjectResourceBuilder):
        self.request_executor = request_executor
        self.local_directory = local_directory
        self.mycloud_directory = mycloud_directory
        self.progress_tracker = tracker
        self.is_encrypted = encryption_password is not None
        self.encryption_password = encryption_password
        self.builder = builder
        self.update_encryptor()


    def update_encryptor(self):
        self.encryptor = Encryptor(self.encryption_password, ENCRYPTION_CHUNK_LENGTH) if self.is_encrypted else None