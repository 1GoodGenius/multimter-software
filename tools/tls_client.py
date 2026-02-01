#!/usr/bin/env python3
"""Minimal TLS client to connect to a TLS/mTLS-enabled ESP32 bridge and perform a HELLO handshake.

Example:
  python tools/tls_client.py --host 192.168.4.1 --port 5000 --cafile ca.pem --cert client.crt --key client.key
"""
import argparse
import socket
import ssl
import struct
import time

FRAME_START = 0xAA
FT_HELLO = 0x01
FT_ACK = 0xF0


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
    crc = crc16(bytes([ft]) + payload)
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


class TLSBridgeClient:
    def __init__(self, host, port, cafile=None, certfile=None, keyfile=None, server_hostname=None):
        self.host = host
        self.port = port
        self.cafile = cafile
        self.certfile = certfile
        self.keyfile = keyfile
        self.server_hostname = server_hostname or host
        self.sock = None

    def connect(self, timeout=5.0):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.cafile)
        if self.certfile and self.keyfile:
            context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        # For self-signed testing, user can set cafile to the CA pem
        raw = socket.create_connection((self.host, self.port), timeout=timeout)
        self.sock = context.wrap_socket(raw, server_hostname=self.server_hostname)
        return True

    def close(self):
        if self.sock:
            try: self.sock.shutdown(socket.SHUT_RDWR)
            except Exception: pass
            self.sock.close()
            self.sock = None

    def send_frame(self, ft, payload=b''):
        f = build_frame(ft, payload)
        self.sock.sendall(f)

    def read_frame(self, timeout=2.0):
        self.sock.settimeout(timeout)
        buf = bytearray()
        end = time.time() + timeout
        while time.time() < end:
            b = self.sock.recv(1)
            if not b:
                continue
            buf += b
            if len(buf) >= 6:
                if buf[0] != FRAME_START:
                    # strip until FRAME_START
                    try:
                        p = buf.index(FRAME_START)
                        buf = buf[p:]
                    except ValueError:
                        buf = bytearray(); continue
                if len(buf) >= 4:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--cafile', help='CA certificate file to validate server')
    parser.add_argument('--cert', help='Client certificate for mTLS')
    parser.add_argument('--key', help='Client private key for mTLS')
    args = parser.parse_args()

    cl = TLSBridgeClient(args.host, args.port, cafile=args.cafile, certfile=args.cert, keyfile=args.key)
    print(f"Connecting to {args.host}:{args.port} ...")
    cl.connect()
    print("Connected (TLS handshake complete)")
    # Send HELLO
    cl.send_frame(FT_HELLO, b'')
    r = cl.read_frame(2.0)
    print('HELLO response:', r)
    cl.close()

if __name__ == '__main__':
    main()
