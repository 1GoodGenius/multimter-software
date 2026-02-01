#!/usr/bin/env python3
"""Provision HMAC key into device EEPROM via serial CLI.
Usage: provision_hmac_key.py --port COM3 --hex 001122..."""
import argparse
import serial
import time

parser = argparse.ArgumentParser()
parser.add_argument('--port', required=True)
parser.add_argument('--baud', type=int, default=115200)
parser.add_argument('--hex', required=True, help='Hex-encoded key (max 128 chars = 64 bytes)')
args = parser.parse_args()

ser = serial.Serial(args.port, args.baud, timeout=1)
# wait a moment
time.sleep(1)
cmd = f"AUTH_SETKEY {args.hex}\n"
ser.write(cmd.encode('ascii'))
# read response lines for up to 2 seconds
deadline = time.time() + 2
while time.time() < deadline:
    line = ser.readline()
    if not line:
        continue
    print(line.decode('ascii', errors='ignore').rstrip())
ser.close()
