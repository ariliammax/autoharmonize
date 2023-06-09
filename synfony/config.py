# config.py
# in synfony


# Useful configuration constants throughout the codebase.
class Config:
    # TODO: delete these eventually, and make args
    CHANNELS = [
        # [FILE, CHUNKS, CHUNK_LENGTH]
        ["The Turn Down/bass",   100, 1.4929],  # CHANNEL 0
        ["The Turn Down/drums",  100, 1.4929],  # CHANNEL 1
        ["The Turn Down/other",  100, 1.4929],  # CHANNEL 2
        ["The Turn Down/vocals", 100, 1.4929],  # CHANNEL 3
    ]

    MACHINES = [
        '10.250.140.244:10000',
        '10.250.78.122:20000',
        '10.250.148.84:30000']

    # [ADDRESS, CHANNELS]
    STREAMS = [
        ['10.250.140.244:10100', [0, 1, 2, 3]],
        ['10.250.78.122:20100', [0, 1, 2, 3]],
        ['10.250.148.84:30100', [0, 1, 2, 3]],
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
    TOLERABLE_DELAY = 0.01

    PYGAME_DELAY = 0.001

    REMOTE_DELAY_SHORT = 0.5
    REMOTE_DELAY_LONG = 5.0
    REMOTE_DELAY_LONG_FREQUENCY = 5


class UIConfig:
    SCREEN_HEIGHT = 640
    SCREEN_WIDTH = 640
    FPS = 60
