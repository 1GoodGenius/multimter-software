#!/usr/bin/env python3
"""Test that host ECDSA signing produces a 64-byte r||s signature and that verification via python `ecdsa` succeeds."""
from ecdsa import SigningKey, VerifyingKey, NIST256p
from hashlib import sha256

# generate ephemeral key
sk = SigningKey.generate(curve=NIST256p)
vk = sk.get_verifying_key()
msg = b'hello firmware'
h = sha256(msg).digest()
sig = sk.sign_digest(h, sigencode=lambda r, s, order: r.to_bytes(32,'big') + s.to_bytes(32,'big'))
assert len(sig) == 64
# verify
r = int.from_bytes(sig[:32], 'big')
s = int.from_bytes(sig[32:], 'big')
# decode back to der for ecdsa lib verify
from ecdsa.util import sigencode_der, sigdecode_der
from ecdsa import util
# verify using raw digest
assert vk.verify_digest(sig, h, sigdecode=lambda der_bytes, order: (r, s))
print('Host sign/verify test passed')
