import abc
from collections import deque

import numpy as np


class DataSource(abc.ABC):
    def __init__(self, source: abc.ABC):
        self.source: abc.ABC = source
        pass

    @abc.abstractmethod
    def query_data(self):
        raise NotImplementedError


class DataBuffer:
    def __init__(self, data_source: DataSource, buffer_size: int = 128):
        self.buffer = deque(maxlen=buffer_size)
        self.data_source = data_source
        self.buffer_size = buffer_size

    def update(self):
        try:
            new_data = self.data_source.query_data()
            self.buffer.append(new_data)
        except Exception as e:
            raise RuntimeError(f"Error querying data source: {e}")

    def get_data(self):
        return np.concatenate(list(self.buffer))
