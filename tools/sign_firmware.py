#!/usr/bin/env python3
"""Sign firmware using ECDSA P-256 and output raw signature (r||s) 64 bytes.
Requires: pip install ecdsa

Usage:
  python tools/sign_firmware.py --key privkey.pem --in firmware.bin --out firmware.sig
"""
import argparse
from ecdsa import SigningKey, NIST256p

parser = argparse.ArgumentParser()
parser.add_argument('--key', required=True, help='PEM private key (EC, P-256)')
parser.add_argument('--in', dest='infile', required=True)
parser.add_argument('--out', dest='outfile', required=True)
args = parser.parse_args()

sk = SigningKey.from_pem(open(args.key).read())
with open(args.infile, 'rb') as f:
    data = f.read()
from hashlib import sha256
h = sha256(data).digest()
sig = sk.sign_digest(h, sigencode=lambda r, s, order: r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))
with open(args.outfile, 'wb') as f:
    f.write(sig)
print('Signature written to', args.outfile)
