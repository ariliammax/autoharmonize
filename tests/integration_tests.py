# test.py

from synfony.config import Config as SConfig

import pytest


# this is a "mock" of `synfony.config.Config` for the purpose of testing
class Config(SConfig):
    MACHINES = [
        'localhost:10000',           # MACHINE 0
        'localhost:20000',           # MACHINE 1
        'localhost:30000']           # MACHINE 2

    # [ADDRESS, CHANNELS]
    STREAMS = [
        ['localhost:10100', [1, 0]],  # MACHINE 0
        ['localhost:20100', [2, 0]],  # MACHINE 1
        ['localhost:30100', [3, 0]],  # MACHINE 2
    ]


# MARK: - communication tests


def test_startup():
    pass


def test_metronome():
    pass


def test_down():
    pass
