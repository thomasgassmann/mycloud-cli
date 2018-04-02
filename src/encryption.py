from Crypto import Random
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
import os, struct, base64


class Encryptor:
    def __init__(self, password, chunk_size):
        self.key = SHA256.new(password.encode()).digest()
        self.chunk_size = chunk_size
        self.first_state = True


    def encrypt(self, source):
        first = self.first_state
        if first:
            self.IV = Random.new().read(AES.block_size)
            self.aes = AES.new(self.key, AES.MODE_CBC, self.IV)
            self.first_state = False
        # Assume last, if chunk size is not met
        # Add padding for message length
        if len(source) != self.chunk_size:
            padding = AES.block_size - len(source) % AES.block_size
            source += bytes([padding]) * padding
        encrypted = self.aes.encrypt(source)
        return self.IV + encrypted if first else encrypted


    def decrypt(self, source):
        first = self.first_state
        if first:
            self.IV = source[:AES.block_size]
            self.aes = AES.new(self.key, AES.MODE_CBC, self.IV)
            self.first_state = False
        decrypted_data = self.aes.decrypt(source[AES.block_size:]) if first else self.aes.decrypt(source)
        # Assume last, if chunk size is not met
        # Cut padding
        if len(source) != self.chunk_size:
            padding = decrypted_data[-1]
            return decrypted_data[:-padding]
        return decrypted_data