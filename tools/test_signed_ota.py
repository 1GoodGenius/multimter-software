#!/usr/bin/env python3
"""Quick test for signed OTA flow (host side). Requires:
  - ecdsa (pip install ecdsa)
  - device connected to COM port

Usage:
  python tools/test_signed_ota.py --port COM3 --file firmware.bin --priv privkey.pem
"""
import argparse
import sys
from tools.file_transfer import SerialConn, send_signed_file

parser = argparse.ArgumentParser()
parser.add_argument('--port', required=True)
parser.add_argument('--file', required=True)
parser.add_argument('--priv', required=False, help='Private key PEM to sign file (P-256)')
parser.add_argument('--sig', required=False, help='Precomputed signature file (r||s 64 bytes)')
args = parser.parse_args()

conn = SerialConn(args.port)
ok = send_signed_file(conn, args.file, privkey_pem=args.priv, signature_path=args.sig)
if ok:
    print('✓ Signed OTA send completed (device should verify and set pending flag)')
    sys.exit(0)
else:
    print('✗ Signed OTA failed')
    sys.exit(1)
