# config.py
# in synfony


# Useful configuration constants throughout the codebase.
class Config:
    INT_LEN = 1024
    INT_MAX_LEN = 1 << 64
    LIST_MAX_LEN = 255
    MACHINES = ['localhost:10000',
                'localhost:20000',
                'localhost:30000']
    STR_MAX_LEN = 280
    TIMEOUT = 2
    CHUNK_MAX_DURATION_MS = 2000
