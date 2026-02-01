#!/usr/bin/env python3
"""Test harness for signed OTA simulation flow.

This script provisions no keys; the device must have the OTA pubkey pre-provisioned via
`AUTH_SETKEY` or `OTA_SET_PUBKEY` before running this test.
"""
import argparse
import time
from tools.file_transfer import SerialConn, send_signed_file

parser = argparse.ArgumentParser()
parser.add_argument('--port', required=True)
parser.add_argument('--file', required=True)
parser.add_argument('--priv', help='Private key PEM to sign file (P-256)')
args = parser.parse_args()

conn = SerialConn(args.port)
print('Provisioning pubkey (example) must be done via OTA_SET_PUBKEY on device')
# Send signed file
ok = send_signed_file(conn, args.file, privkey_pem=args.priv)
if not ok:
    print('Failed to send signed file')
    raise SystemExit(1)
# Wait a moment for device to verify
time.sleep(1)
# Check pending flag via serial command
conn.ser.write(b'OTA_CHECK\n')
# read lines
deadline = time.time() + 2
while time.time() < deadline:
    l = conn.ser.readline()
    if l:
        print(l.decode().strip())

print('Now apply (simulated): sending OTA_REBOOT_APPLY...')
conn.ser.write(b'OTA_REBOOT_APPLY\n')
deadline = time.time() + 3
while time.time() < deadline:
    l = conn.ser.readline()
    if l: print(l.decode().strip())
print('NOTE: On real device the bootloader must check the EEPROM pending flag and perform flash/rollback. This test simulates host-side steps only.')
