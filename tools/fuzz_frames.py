#!/usr/bin/env python3
"""Generate random byte streams and ensure parse_frame is robust."""
import random
from tools.file_transfer import parse_frame

for i in range(1000):
    data = bytes(random.getrandbits(8) for _ in range(random.randint(0, 64)))
    try:
        _ = parse_frame(data)
    except Exception as e:
        print("Parsing raised an exception on random data:", e)
        raise
print("Fuzzing completed without exceptions")
