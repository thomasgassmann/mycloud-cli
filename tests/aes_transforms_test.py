import os
from Crypto.Cipher import AES
from mycloud.streamapi.transforms import AES256CryptoTransform


def test_aes_transform_padding_is_applied():
    transform = AES256CryptoTransform('test')
    first_bytes = os.urandom(AES.block_size)
    # use uneven offset
    second_bytes = os.urandom(AES.block_size + 1)
    first = transform.up_transform(first_bytes)
    second_with_padding = transform.up_transform(second_bytes, last=True)

    transform.reset_state()

    first_down = transform.down_transform(first)
    second_down = transform.down_transform(second_with_padding, last=True)
    assert first_down + second_down == first_bytes + second_bytes
