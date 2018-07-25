from streamapi import StreamTransform


class AES256EncryptTransform(StreamTransform):

    def __init__(self, password):
        super().__init__('aes256_encrypt')


    def reset_state(self):
        return

    
    def transform(self, byte_sequence: bytes) -> bytes:
        return byte_sequence


class AES256DecryptTransform(StreamTransform):

    def __init__(self, password):
        super().__init__('aes256_decrypt')


    def reset_state(self):
        return

    
    def transform(self, byte_sequence: bytes) -> bytes:
        return byte_sequence