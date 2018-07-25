from streamapi import StreamTransform
from Crypto import Random
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.py3compat import bchr, bord
from constants import ENCRYPTION_CHUNK_LENGTH
from abc import ABC
import os, base64


def derive_key(password: str):
    return SHA256.new(password.encode()).digest()


class AES256CrytoTransformBase(StreamTransform):

    def __init__(self, name: str, password: str):
        super().__init__('aes256_encrypt')
        self._key = derive_key(password)
        self._first = True
        self._finished_last = False


    def reset_state(self):
        self._first = True
        self._finished_last = False


class AES256EncryptTransform(AES256CrytoTransformBase):

    def __init__(self, password):
        super().__init__('aes256_encrypt', password)

    
    def transform(self, byte_sequence: bytes, last: bool=False) -> bytes:
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


class AES256DecryptTransform(AES256CrytoTransformBase):

    def __init__(self, password):
        super().__init__('aes256_decrypt', password)

    
    def transform(self, byte_sequence: bytes, last: bool=False) -> bytes:
        if self._finished_last:
            return bytes([])

        first = self._first
        if first:
            iv = byte_sequence[:AES.block_size]
            self._aes = AES.new(self._key, AES.MODE_CBC, iv)
            self._first = False
        decrypted_data = self._aes.decrypt(byte_sequence[AES.block_size:]) if first else self._aes.decrypt(byte_sequence)
        # Cut padding
        if last:
            padding = bord(decrypted_data[-1])
            if decrypted_data[-padding:] != bchr(padding) * padding:
                raise ValueError('PKCS#7 padding is incorrect')
            self._finished_last = True
            return decrypted_data[:-padding]
        return decrypted_data