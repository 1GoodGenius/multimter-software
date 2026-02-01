#!/usr/bin/env python3
"""
Invoke integration test on connected device and return non-zero on failure.
Usage: python tools/integration_ci.py --port COM3
"""
import argparse
from comm_helper import Comm, FT_INTEGRATION_REPORT
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--port', required=True)
args = parser.parse_args()

c = Comm(args.port)
# send run_integration and request streaming disabled; we only need summary
c.send_frame(0x12, bytes([0]))
resp = c.read_frame(10.0)
if not resp:
    print('No ACK from device; aborting')
    sys.exit(2)
# read the report
rep = c.read_frame(15.0)
if not rep:
    print('No integration report received; aborting')
    sys.exit(3)
if rep[0] != FT_INTEGRATION_REPORT:
    print('Unexpected frame type:', rep)
    sys.exit(4)
payload = rep[1]
flags = payload[:4]
summary = payload[4:].decode('ascii', errors='ignore').rstrip('\x00')
print('Integration flags:', list(flags), 'summary:', summary)
# Expect all flags to be 1 for pass
if all([b == 1 for b in flags]):
    print('Integration PASSED')
    sys.exit(0)
else:
    print('Integration FAILED')
    sys.exit(1)
