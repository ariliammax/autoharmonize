# config.py
# in synfony


# Useful configuration constants throughout the codebase.
class Config:
    # TODO: delete these eventually, and make args
    CHANNELS = [
        # [FILE, CHUNKS, CHUNK_LENGTH]
        # ["The Turn Down/bass",   100, 1.4929], # CHANNEL 0
        # ["The Turn Down/drums",  100, 1.4929], # CHANNEL 1
        # ["The Turn Down/other",  100, 1.4929], # CHANNEL 2
        ["The Turn Down/vocals", 100, 1.4929], # CHANNEL 3
    ]
    MACHINES = ['localhost:10000', # MACHINE 0
                'localhost:20000', # MACHINE 1
                'localhost:30000'] # MACHINE 2
    STREAMS = [
        # [ADDRESS, CHANNELS]
        ["localhost:10100", [0]], # [0, 3]], # MACHINE 0
        ["localhost:20100", [0]], # [1, 3]], # MACHINE 1
        ["localhost:30100", [0]], # [2, 3]], # MACHINE 2
    ]

    INT_MAX_LEN = 1 << 64
    LIST_MAX_LEN = 255
    PACKET_MAX_LEN = 1024
    STR_MAX_LEN = 280

    HANDSHAKE_ENABLED = False
    HANDSHAKE_TIMEOUT = 0.3
    HANDSHAKE_INTERVAL = 1.1
    HEARTBEAT_TIMEOUT = 1
    TIMEOUT = 1
    TOLERABLE_DELAY = 0.1


class UIConfig:
    SCREEN_HEIGHT = 640
    SCREEN_WIDTH = 640
    fps=60
