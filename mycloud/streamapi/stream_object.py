from abc import ABC, abstractmethod
from enum import Enum


class StreamDirection(Enum):
    Up = 0
    Down = 1


class CloudStream(ABC):

    def __init__(self,
                 stream_direction: StreamDirection,
                 continued_append_starting_index: int):
        self.stream_direction = stream_direction
        self.continued_append_starting_index = continued_append_starting_index
        self._finished = False

    def finished(self):
        self._finished = True

    @abstractmethod
    def close(self):
        raise NotImplementedError()

    def is_finished(self):
        return self._finished


class UpStream(CloudStream):

    def __init__(self, continued_append_starting_index: int = 0):
        super().__init__(StreamDirection.Up, continued_append_starting_index)

    @abstractmethod
    def read(self, length: int):
        raise NotImplementedError()


class DownStream(CloudStream):

    def __init__(self, continued_append_starting_index: int = 0):
        super().__init__(StreamDirection.Down, continued_append_starting_index)

    @abstractmethod
    def write(self, data):
        raise NotImplementedError()


class DefaultDownStream(DownStream):

    def __init__(self, stream, continued_append_starting_index: int = 0):
        super().__init__(continued_append_starting_index)
        self._stream = stream

    def write(self, data):
        self._stream.write(data)

    def close(self):
        self._stream.close()


class DefaultUpStream(UpStream):

    def __init__(self, stream, continued_append_starting_index: int = 0):
        super().__init__(continued_append_starting_index)
        self._stream = stream

    def read(self, length: int):
        return self._stream.read(length)

    def close(self):
        self._stream.close()
