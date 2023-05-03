# config.py
# in synfony


# Useful configuration constants throughout the codebase.
class Config:
    # TODO: delete these eventually, and make args
    CHANNELS = [
        # [FILE, CHUNKS, CHUNK_LENGTH]
        ["The Turn Down/bass",   100, 1.4929], # CHANNEL 0
        ["The Turn Down/drums",  100, 1.4929], # CHANNEL 1
        ["The Turn Down/other",  100, 1.4929], # CHANNEL 2
        ["The Turn Down/vocals", 100, 1.4929], # CHANNEL 3
    ]
    MACHINES = ['localhost:10005', # MACHINE 0
                'localhost:20005', # MACHINE 1
                'localhost:30005'] # MACHINE 2
    STREAMS = [
        # [ADDRESS, CHANNELS]
        ['localhost:10105', [0, 1, 2, 3]], # MACHINE 0
        ['localhost:20105', [0, 1, 2, 3]], # MACHINE 1
        ['localhost:30105', [0, 1, 2, 3]], # MACHINE 2

    INT_MAX_LEN = 1 << 64
    LIST_MAX_LEN = 255
    PACKET_MAX_LEN = 1024
    STR_MAX_LEN = 280

    HANDSHAKE_ENABLED = True
    HANDSHAKE_TIMEOUT = 0.3
    HANDSHAKE_INTERVAL = 1.1
    HEARTBEAT_TIMEOUT = 1
    TIMEOUT = 1
    TOLERABLE_DELAY = 0.1

    REMOTE_DELAY_SHORT = 0.5
    REMOTE_DELAY_LONG  = 5.0
    REMOTE_DELAY_LONG_FREQUENCY = 5


class UIConfig:
    SCREEN_HEIGHT = 640
    SCREEN_WIDTH = 640
    fps=60
