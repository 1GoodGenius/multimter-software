#!/usr/bin/env python3
"""Test helper to validate TLS bridge connectivity.

Example:
  python tools/test_tls_bridge.py --host 127.0.0.1 --port 5001 --cafile ca.pem --cert client.crt --key client.key
"""
import argparse
import os, sys
# ensure project root is on sys.path so relative imports work when invoked directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tools.tls_client import TLSBridgeClient

parser = argparse.ArgumentParser()
parser.add_argument('--host', required=True)
parser.add_argument('--port', type=int, default=5000)
parser.add_argument('--cafile')
parser.add_argument('--cert')
parser.add_argument('--key')
args = parser.parse_args()

client = TLSBridgeClient(args.host, args.port, cafile=args.cafile, certfile=args.cert, keyfile=args.key)
try:
    client.connect()
    print('✓ TLS connection established')
    # Send HELLO and expect ACK
    client.send_frame(0x01, b'')
    r = client.read_frame(2.0)
    if r:
        print('✓ HELLO response received:', r)
        sys.exit(0)
    else:
        print('✗ No HELLO response')
        sys.exit(2)
except Exception as e:
    print('✗ TLS connection failed:', e)
    sys.exit(1)
finally:
    client.close()
