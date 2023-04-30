# config.py
# in synfony.common

# Useful configuration constants throughout the codebase.
class Config:
    MACHINES = [('localhost', 10000),
                ('localhost', 20000),
                ('localhost', 30000)]
    STR_MAX_LEN = 280
    LIST_MAX_LEN = 255
    INT_MAX_LEN = 1 << 64
