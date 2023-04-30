# config.py
# in synfony


# Useful configuration constants throughout the codebase.
class Config:
    CHANNELS = [
        "The Turn Down/bass",
        "The Turn Down/drums",
        "The Turn Down/other",
        "The Turn Down/vocals",
    ]
    INT_LEN = 1024
    INT_MAX_LEN = 1 << 64
    LIST_MAX_LEN = 255
    MACHINES = ['localhost:10001',
                'localhost:20001',
                'localhost:30001']
    STR_MAX_LEN = 280
    TIMEOUT = 2

class UIConfig:
    SCREEN_HEIGHT = 480
    SCREEN_WIDTH = 640
    fps=60
