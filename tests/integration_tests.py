# integration_tests.py

from synfony.config import Config as SConfig
from synfony.sockets import BaseSockets
from synfony.streamer import BaseStreamer
from synfony.ui import BaseUI

import pytest


# MARK: - Mock classes


class Config(SConfig):
    """this is a "mock" of `synfony.config.Config` for the purpose of testing
    """
    MACHINES = [
        'localhost:10000',         # MACHINE 0
        'localhost:20000',         # MACHINE 1
        'localhost:30000']         # MACHINE 2

    # [ADDRESS, CHANNELS]
    STREAMS = [
        ['localhost:10100', [0]],  # MACHINE 0
        ['localhost:20100', [0]],  # MACHINE 1
        ['localhost:30100', [0]],  # MACHINE 2
    ]


# TODO: do we want / need `MockSocket`?
class MockSocket(object):
    def __init__(self, key, end=None):
        self.key = key
        self.stream = []
        self.timeout = timeout


class MockSockets(BaseSockets):
    sockets = {}

    @classmethod
    def accept(cls, s):
        raise NotImplementedError()

    @classmethod
    def close(cls, s):
        cls.sockets.pop(s.key)

    @classmethod
    def recv(cls, connection):
        raise NotImplementedError()

    @classmethod
    def send(cls, connection, data):
        raise NotImplementedError()

    @classmethod
    def sendall(cls, s, data):
        raise NotImplementedError()

    @classmethod
    def shutdown(cls, s):
        pass

    @classmethod
    def start_socket(cls,
                     machine_address,
                     timeout=None,
                     bind=False,
                     connect=False):
        raise NotImplementedError()


class MockStreamer(BaseStreamer):
    def __init__(self, channel_id):
        self.channel_id = channel_id

    def init(self):
        pass

    def event(self, event):
        pass

    def get_chunk(self, chunk):
        pass

    def get_current_time(self):
        pass

    def get_last_time(self):
        pass

    def get_num_channels(self):
        return len(Config.CHANNELS)

    def get_title(self):
        pass

    def get_total_time(self):
        pass

    def get_volume(self):
        pass

    def is_playing(self):
        pass

    def is_seeking(self):
        pass

    def schedule_seek(self, chunk, interval, playing):
        pass

    def seek(self, chunk, playing):
        pass

    def sync(self, state):
        pass

    def shutdown(self):
        pass


class MockUI(BaseUI):
    def __init__(self):
        self.streamers = []
        self.event_queue = []

    @abstractmethod
    def init(machine_id):
        pass

    @abstractmethod
    def start_loading():
        pass

    @abstractmethod
    def stop_loading():
        pass


# MARK: - communication tests


def impl_test_startup():
    pass


def test_metronome():
    pass


def test_down():
    pass
