from Crypto import Random
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.py3compat import bchr, bord
import os
import base64
from mycloud.constants import ENCRYPTION_CHUNK_LENGTH
from mycloud.streamapi.transforms.stream_transform import StreamTransform


def derive_key(password: str):
    return SHA256.new(password.encode()).digest()


class AES256CryptoTransform(StreamTransform):

    def __init__(self, password: str):
        super().__init__('aes256_transform')
        self._key = derive_key(password)
        self._first = True
        self._finished_last = False

    def reset_state(self):
        self._first = True
        self._finished_last = False
        self._aes = None

    def up_transform(self, byte_sequence: bytes, last: bool=False):
        if self._finished_last:
            return bytes([])

        # Add padding for message length
        if last:
            padding = AES.block_size - len(byte_sequence) % AES.block_size
            byte_sequence += bchr(padding) * padding
            self._finished_last = True

        if self._first:
            self._first = False
            iv = Random.new().read(AES.block_size)
            self._aes = AES.new(self._key, AES.MODE_CBC, iv)
            return iv + self._aes.encrypt(byte_sequence)

        return self._aes.encrypt(byte_sequence)

    def down_transform(self, byte_sequence: bytes, last: bool=False):
        if self._finished_last:
            return bytes([])

        first = self._first
        if first:
            iv = byte_sequence[:AES.block_size]
            self._aes = AES.new(self._key, AES.MODE_CBC, iv)
            self._first = False
        decrypted_data = self._aes.decrypt(
            byte_sequence[AES.block_size:]) if first else self._aes.decrypt(byte_sequence)
        # Cut padding
        if last:
            padding = bord(decrypted_data[-1])
            if decrypted_data[-padding:] != bchr(padding) * padding:
                raise ValueError('PKCS#7 padding is incorrect')
            self._finished_last = True
            return decrypted_data[:-padding]
        return decrypted_data