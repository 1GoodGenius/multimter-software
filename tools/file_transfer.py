#!/usr/bin/env python3
"""Host-side file-transfer helper using the framed protocol.

Usage:
  python tools/file_transfer.py --port COM3 --send firmware.bin --chunk-size 1024
  python tools/file_transfer.py --tcp 127.0.0.1:5000 --send firmware.bin

This is intentionally small and focuses on reliability via per-chunk ACKs and retries.
"""

import argparse
import os
import struct
import socket
import time

FRAME_START = 0xAA

# Frame types (must match firmware values)
FT_FILE_TRANSFER_START = 0x30
FT_FILE_TRANSFER_CHUNK = 0x31
FT_FILE_TRANSFER_END = 0x32
FT_FILE_TRANSFER_ACK = 0x33
FT_FILE_TRANSFER_NACK = 0x34
FT_ACK = 0xF0
FT_NACK = 0xF1


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def build_frame(ft: int, payload: bytes) -> bytes:
    frame_len = len(payload) + 1
    header = struct.pack('>BHB', FRAME_START, frame_len, ft)
    body = bytes([ft]) + payload
    crc = crc16(body)
    return header + payload + struct.pack('>H', crc)


def parse_frame(buf: bytes):
    try:
        if buf[0] != FRAME_START:
            return None
        frame_len = (buf[1] << 8) | buf[2]
        ft = buf[3]
        payload = buf[4:4+frame_len-1]
        crc_in = (buf[4+frame_len-1] << 8) | buf[4+frame_len]
        calc = crc16(bytes([ft]) + payload)
        if calc != crc_in:
            return None
        return ft, payload
    except Exception:
        return None


class SerialConn:
    def __init__(self, port, baud=115200, timeout=1.0):
        import serial
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def send_raw(self, data: bytes):
        self.ser.write(data)

    def read_raw(self, timeout=2.0):
        deadline = time.time() + timeout
        buf = bytearray()
        while time.time() < deadline:
            b = self.ser.read(1)
            if not b:
                continue
            buf += b
            if len(buf) >= 6:
                if buf[0] != FRAME_START:
                    try:
                        p = buf.index(FRAME_START)
                        buf = buf[p:]
                        continue
                    except ValueError:
                        buf = bytearray()
                        continue
                frame_len = (buf[1] << 8) | buf[2]
                total_len = 4 + (frame_len - 1) + 2
                if len(buf) >= total_len:
                    candidate = bytes(buf[:total_len])
                    parsed = parse_frame(candidate)
                    if parsed:
                        return parsed
                    else:
                        buf = buf[1:]
        return None


class TCPConn:
    def __init__(self, host, port, timeout=3.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)

    def send_raw(self, data: bytes):
        self.sock.sendall(data)

    def read_raw(self, timeout=2.0):
        self.sock.settimeout(timeout)
        buf = bytearray()
        try:
            while True:
                b = self.sock.recv(1)
                if not b:
                    break
                buf += b
                if len(buf) >= 6:
                    if buf[0] != FRAME_START:
                        try:
                            p = buf.index(FRAME_START)
                            buf = buf[p:]
                            continue
                        except ValueError:
                            buf = bytearray()
                            continue
                    frame_len = (buf[1] << 8) | buf[2]
                    total_len = 4 + (frame_len - 1) + 2
                    if len(buf) >= total_len:
                        candidate = bytes(buf[:total_len])
                        parsed = parse_frame(candidate)
                        if parsed:
                            return parsed
                        else:
                            buf = buf[1:]
        except socket.timeout:
            return None
        return None


def send_frame(conn, ft, payload=b''):
    f = build_frame(ft, payload)
    conn.send_raw(f)


def send_frame_with_ack(conn, ft, payload=b'', timeout=1.0, retries=4):
    for attempt in range(retries):
        send_frame(conn, ft, payload)
        start = time.time()
        while time.time() - start < timeout:
            frame = conn.read_raw(timeout - (time.time() - start))
            if not frame:
                continue
            ftype, pl = frame
            if ftype == FT_FILE_TRANSFER_ACK and len(pl) >= 1 and pl[0] == ft:
                return True, pl[1:]
            if ftype == FT_FILE_TRANSFER_NACK and len(pl) >= 1 and pl[0] == ft:
                return False, pl[1:]
            if ftype == FT_ACK and len(pl) >= 1 and pl[0] == ft:
                return True, pl[1:]
            if ftype == FT_NACK and len(pl) >= 1 and pl[0] == ft:
                return False, pl[1:]
        # retry
    return False, b''


def chunk_file(path, chunk_size=1024):
    with open(path, 'rb') as f:
        idx = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield idx, data
            idx += 1


def send_file(conn, path, chunk_size=1024):
    size = os.path.getsize(path)
    filename = os.path.basename(path).encode('utf-8')
    if len(filename) > 255:
        raise ValueError('Filename too long')

    # start payload: filename_len(1) + filename + filesize(8BE) + chunk_size(2BE)
    payload = bytes([len(filename)]) + filename + struct.pack('>Q', size) + struct.pack('>H', chunk_size)
    ok, resp = send_frame_with_ack(conn, FT_FILE_TRANSFER_START, payload, timeout=2.0, retries=3)
    if not ok:
        print('Start not acknowledged, aborting')
        return False
    print('Start accepted, sending chunks...')

    for idx, data in chunk_file(path, chunk_size):
        payload = struct.pack('>I', idx) + data
        ok, r = send_frame_with_ack(conn, FT_FILE_TRANSFER_CHUNK, payload, timeout=2.0, retries=4)
        if not ok:
            print(f'Chunk {idx} failed after retries, aborting')
            return False
        print(f'Chunk {idx} ACK')

    # end frame: optional final CRC
    # compute file CRC
    with open(path, 'rb') as f:
        whole = f.read()
    file_crc = crc16(whole)
    payload = struct.pack('>H', file_crc)
    ok, r = send_frame_with_ack(conn, FT_FILE_TRANSFER_END, payload, timeout=3.0, retries=3)
    if not ok:
        print('End not acknowledged')
        return False
    print('File transfer complete')
    return True


def send_signed_file(conn, path, privkey_pem=None, signature_path=None, chunk_size=1024):
    """Send a signed file. Either provide a private key PEM (P-256) to sign locally or
    a precomputed signature file (64 bytes raw r||s) via signature_path.
    """
    # if signature_path provided, read signature. Otherwise sign using privkey
    if signature_path:
        with open(signature_path, 'rb') as f:
            sig = f.read()
    else:
        # require ecdsa package
        try:
            from ecdsa import SigningKey, NIST256p
            from hashlib import sha256
        except Exception as e:
            raise RuntimeError('Signing requires python ecdsa package: pip install ecdsa') from e
        if not privkey_pem:
            raise ValueError('Private key PEM required if signature_path not provided')
        sk = SigningKey.from_pem(open(privkey_pem).read())
        with open(path, 'rb') as f:
            data = f.read()
        h = sha256(data).digest()
        sig = sk.sign_digest(h, sigencode=lambda r, s, order: r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))

    if len(sig) != 64:
        raise ValueError('Signature must be 64 bytes (r||s)')

    # do normal file send
    ok = send_file(conn, path, chunk_size)
    if not ok:
        return False

    # Send end frame with signature payload (signature only)
    ok, r = send_frame_with_ack(conn, FT_FILE_TRANSFER_END, sig, timeout=5.0, retries=4)
    if not ok:
        print('Signed end not acknowledged')
        return False
    print('Signed file transfer complete')
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help='Serial port (e.g., COM3 or /dev/ttyACM0)')
    parser.add_argument('--tcp', help='TCP host:port (e.g., host:5000)')
    parser.add_argument('--send', help='File to send')
    parser.add_argument('--chunk-size', type=int, default=1024, help='Chunk size in bytes')
    args = parser.parse_args()

    conn = None
    if args.tcp:
        host, port = args.tcp.split(':')
        conn = TCPConn(host, int(port))
    elif args.port:
        conn = SerialConn(args.port)
    else:
        parser.error('Specify --port or --tcp')

    if args.send:
        ok = send_file(conn, args.send, chunk_size=args.chunk_size)
        print('Done:', ok)

if __name__ == '__main__':
    main()
