from abc import ABC, abstractmethod


class StreamTransform(ABC):
    """
    Input of up_transform must always equal output of down_transform.
    """

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    @abstractmethod
    def reset_state(self):
        raise NotImplementedError()

    @abstractmethod
    def up_transform(self, byte_sequence: bytes, last: bool = False):
        raise NotImplementedError()

    @abstractmethod
    def down_transform(self, byte_sequence: bytes, last: bool = False):
        raise NotImplementedError()
