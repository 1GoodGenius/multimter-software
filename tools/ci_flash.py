#!/usr/bin/env python3
"""CI helper: attempt to flash an AVR device if DEVICE_PORT is set in environment.

This is intentionally conservative and requires the `AVRDUDE_CMD` env variable to be set
by the CI runner to avoid hardcoding commands.
"""
import os
import sys
import subprocess

PORT = os.environ.get('DEVICE_PORT')
AVR_CMD = os.environ.get('AVRDUDE_CMD')

if not PORT or not AVR_CMD:
    print('DEVICE_PORT or AVRDUDE_CMD not set; skipping device flash.')
    sys.exit(0)

cmd = AVR_CMD.format(port=PORT)
print('Running:', cmd)
ret = subprocess.call(cmd, shell=True)
if ret != 0:
    print('Flashing failed:', ret)
    sys.exit(ret)
print('Flashing successful')
