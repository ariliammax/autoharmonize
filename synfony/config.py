# config.py
# in synfony


# Useful configuration constants throughout the codebase.
class Config:
    CHANNELS = [
        # [FILE, CHUNKS, CHUNK_LENGTH]
        ["The Turn Down/bass", 100, 1.4929],
        ["The Turn Down/drums", 100, 1.4929],
        ["The Turn Down/other", 100, 1.4929],
        ["The Turn Down/vocals", 100, 1.4929],
    ]
    PACKET_MAX_LEN = 1024
    INT_MAX_LEN = 1 << 64
    LIST_MAX_LEN = 255
    MACHINES = ['localhost:10000',
                'localhost:20000',
                'localhost:30000']
    STR_MAX_LEN = 280
    TOLERABLE_DELAY = 0.1

    HANDSHAKE_TIMEOUT = 0.1
    HANDSHAKE_INTERVAL = 1.001
    HEARTBEAT_TIMEOUT = 1


class UIConfig:
    SCREEN_HEIGHT = 480
    SCREEN_WIDTH = 640
    fps=60
