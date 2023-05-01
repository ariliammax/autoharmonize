# enums.py
# in synfony

from enum import Enum


# The possible user events (and which are serialized in the wire)
class EventCode(Enum):
    NONE = 0
    PAUSE = 1 << 0
    PLAY = 1 << 1
    SEEK = 1 << 2
    VOLUME = 1 << 3


# The operation codes for all endpoints (and which are serialized in the wire).
class OperationCode(Enum):
    HEARTBEAT = 0
    IDENTITY = 1
