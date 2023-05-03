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
    MACHINES = ['10.250.140.244:10001', # MACHINE 0
                 '10.250.78.122:20001', # MACHINE 1
                 '10.250.148.84:30001'] # MACHINE 2
    STREAMS = [
        # [ADDRESS, CHANNELS]
        ["10.250.140.244:10101", [1, 0]], # MACHINE 0
        [ "10.250.78.122:20101", [2, 0]], # MACHINE 1
        [ "10.250.148.84:30101", [3, 0]], # MACHINE 2
    ]

    INT_MAX_LEN = 1 << 64
    LIST_MAX_LEN = 255
    PACKET_MAX_LEN = 1024
    STR_MAX_LEN = 280

    HANDSHAKE_ENABLED = True
    HANDSHAKE_TIMEOUT = 0.05
    HANDSHAKE_INTERVAL = 0.25
    HEARTBEAT_TIMEOUT = 0.2
    TIMEOUT = 1
    TOLERABLE_DELAY = 0.1

    PYGAME_DELAY = 0.001

    REMOTE_DELAY_SHORT = 0.5
    REMOTE_DELAY_LONG  = 5.0
    REMOTE_DELAY_LONG_FREQUENCY = 5


class UIConfig:
    SCREEN_HEIGHT = 640
    SCREEN_WIDTH = 640
    fps=60
