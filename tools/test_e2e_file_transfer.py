#!/usr/bin/env python3
"""
End-to-End File Transfer Test Guide

This document and associated test script shows how to test the complete file transfer 
workflow with authentication and communication manager integration.

Prerequisites:
  - Arduino Mega with compiled firmware (see arduino_firmware/README.md)
  - Device connected via USB serial
  - Python 3.8+ with pyserial installed

Test steps:
  1. Flash firmware to Mega
  2. Connect USB serial
  3. Run authentication test
  4. Run file transfer test
"""

import sys
import time
import serial
import hmac
import hashlib
import struct
from tools.file_transfer import SerialConn, send_frame_with_ack, FT_HELLO, FT_AUTH

def test_hello(port='COM3', baud=115200):
    """Test HELLO frame exchange"""
    print("Step 1: Testing HELLO frame...")
    conn = SerialConn(port, baud)
    
    # Send HELLO
    ok, resp = send_frame_with_ack(conn, FT_HELLO, b'', timeout=2.0)
    if not ok:
        print("  ✗ HELLO not acknowledged")
        return False
    
    print(f"  ✓ HELLO ACK received: {resp.decode('utf-8', errors='ignore')}")
    return True


def test_auth(port='COM3', baud=115200, token='multimeter-default-token', hmac_key=None):
    """Test AUTH frame exchange (supports HMAC key hex)"""
    print("Step 2: Testing AUTH frame...")
    conn = SerialConn(port, baud)
    time.sleep(0.5)
    
    if hmac_key:
        key = bytes.fromhex(hmac_key)
        ts = int(time.time()) & 0xFFFFFFFF
        ts_bytes = struct.pack('>I', ts)
        digest = hmac.new(key, ts_bytes, hashlib.sha256).digest()
        payload = ts_bytes + digest[:16]
    else:
        payload = token.encode('utf-8')

    ok, resp = send_frame_with_ack(conn, FT_AUTH, payload, timeout=2.0)
    if not ok:
        print("  ✗ AUTH not acknowledged")
        return False
    
    if len(resp) >= 1 and resp[0] == 1:
        print("  ✓ AUTH successful (token accepted)")
        return True
    else:
        print("  ✗ AUTH failed (token rejected)")
        return False


def test_file_transfer(port='COM3', filename='test_firmware.bin', baud=115200):
    """Test file transfer flow"""
    print("Step 3: Testing file transfer...")
    from tools.file_transfer import send_file
    conn = SerialConn(port, baud)
    time.sleep(0.5)
    
    ok = send_file(conn, filename, chunk_size=512)
    if ok:
        print("  ✓ File transfer completed successfully")
        return True
    else:
        print("  ✗ File transfer failed")
        return False


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='COM3', help='Serial port')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
    parser.add_argument('--token', default='multimeter-default-token', help='Auth token')
    parser.add_argument('--hmac-key', default=None, help='Hex HMAC key for HMAC-based auth')
    parser.add_argument('--file', help='File to transfer')
    args = parser.parse_args()
    
    print("="*60)
    print("End-to-End File Transfer & Auth Test")
    print("="*60)
    
    results = {
        'HELLO': test_hello(args.port, args.baud),
        'AUTH': test_auth(args.port, args.baud, args.token),
    }
    
    if args.file:
        results['FILE_TRANSFER'] = test_file_transfer(args.port, args.file, args.baud)
    
    print("\n" + "="*60)
    print("Results:")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("="*60)
    sys.exit(0 if all_passed else 1)
