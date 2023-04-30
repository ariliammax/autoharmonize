# enums.py
# in synfony

from enum import Enum


# The possible user events (and which are serialized in the wire)
class EventCode(Enum):
    PAUSE = 0
    PLAY = 1
    SEEK = 2


# The operation codes for all endpoints (and which are serialized in the wire).
class OperationCode(Enum):
    HEARTBEAT = 0
    IDENTITY = 1
