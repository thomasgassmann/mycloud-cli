from abc import ABC, abstractmethod


class StreamTransform(ABC):

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    @abstractmethod
    def reset_state(self):
        raise NotImplementedError()

    @abstractmethod
    def transform(self, byte_sequence: bytes, last: bool=False) -> bytes:
        raise NotImplementedError()
