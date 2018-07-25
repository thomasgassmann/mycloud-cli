from streamapi import UpStream, StreamTransform, UpStreamExecutor, StreamDirection, FileMetadata
from streamapi.transforms import AES256EncryptTransform
from mycloudapi import MyCloudRequestExecutor
from mycloudapi.auth import MyCloudAuthenticator

authenticator = MyCloudAuthenticator()
authenticator.set_bearer_auth('')
executor = MyCloudRequestExecutor(authenticator)

class UpFileStream(UpStream):

    def __init__(self, file_stream):
        super().__init__()
        self.file_stream = file_stream


    def read(self, length: int):
        return self.file_stream.read(length)

    
    def close(self):
        return self.file_stream.close()


metadata = FileMetadata('/Drive/test/text', '2.0', True)
aes_transform = AES256EncryptTransform('test')
metadata.add_transform(aes_transform)

stream = UpFileStream(open('A:\\uploadcommand.txt', 'rb'))

upstreamer = UpStreamExecutor(executor)
upstreamer.upload_stream(stream, metadata)