#!/usr/bin/env python3
import struct
from comm_helper import build_frame, parse_frame, FT_PROFILE_EXPORT, FT_RUN_INTEGRATION, FT_ACK, FT_AUTH

# Simple round-trip tests

def test_roundtrip_simple():
    payload = b"\x01"
    frame = build_frame(FT_PROFILE_EXPORT, payload)
    parsed = parse_frame(frame)
    assert parsed is not None
    ft, pl = parsed
    assert ft == FT_PROFILE_EXPORT
    assert pl == payload


def test_run_integration_payload():
    payload = b"\x01" # stream flag
    frame = build_frame(FT_RUN_INTEGRATION, payload)
    parsed = parse_frame(frame)
    assert parsed is not None
    ft, pl = parsed
    assert ft == FT_RUN_INTEGRATION
    assert pl == payload


def test_ack_parse():
    # Build an ACK for FT_PROFILE_EXPORT with extra payload
    ack_payload = bytes([FT_PROFILE_EXPORT, 0x01, 0x02])
    frame = build_frame(FT_ACK, ack_payload)
    parsed = parse_frame(frame)
    assert parsed is not None
    ft, pl = parsed
    assert ft == FT_ACK
    assert pl == ack_payload


def test_hmac_payload_build():
    # Given a key and timestamp, build an HMAC auth payload and verify digest length
    import hmac as _hmac, hashlib as _hashlib
    key = b"\x01\x02\x03\x04"
    ts = 0x5F3759DF
    ts_bytes = struct.pack('>I', ts)
    digest = _hmac.new(key, ts_bytes, _hashlib.sha256).digest()
    payload = ts_bytes + digest[:16]
    # payload length should be 4 + 16
    assert len(payload) == 20
    # If we build a frame and parse it, we should recover the same payload
    frame = build_frame(FT_AUTH, payload)
    parsed = parse_frame(frame)
    assert parsed is not None
    ft, pl = parsed
    assert ft == FT_AUTH
    assert pl == payload

if __name__ == '__main__':
    test_roundtrip_simple()
    test_run_integration_payload()
    test_ack_parse()
    test_hmac_payload_build()
    print('comm_helper tests passed')
