# config.py
# in synfony


# Useful configuration constants throughout the codebase.
class Config:
    # TODO: delete these eventually, and make args
    CHANNELS = [
        # [FILE, CHUNKS, CHUNK_LENGTH]
        ["The Turn Down/bass", 100, 1.4929],
        ["The Turn Down/drums", 100, 1.4929],
        ["The Turn Down/other", 100, 1.4929],
        ["The Turn Down/vocals", 100, 1.4929],
    ]
    MACHINES = ['localhost:10031',
                'localhost:20031',
                'localhost:30031']
    # TODO: add STREAMING_ADDRESSES

    INT_MAX_LEN = 1 << 64
    LIST_MAX_LEN = 255
    PACKET_MAX_LEN = 1024
    STR_MAX_LEN = 280

    HANDSHAKE_TIMEOUT = 0.3
    HANDSHAKE_INTERVAL = 5.1
    HEARTBEAT_TIMEOUT = 5
    TIMEOUT = 1
    TOLERABLE_DELAY = 0.1


class UIConfig:
    SCREEN_HEIGHT = 640
    SCREEN_WIDTH = 640
    fps=60
