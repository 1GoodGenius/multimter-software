#!/usr/bin/env python3
"""
Minimal host helper for Communication Manager framed protocol.
Usage examples:
  ./comm_helper.py --port COM3 profile_export 1
  ./comm_helper.py --port COM3 run_integration --stream
"""
import argparse
import serial
import struct
import time
import hmac
import hashlib

FRAME_START = 0xAA

# Frame types
FT_PROFILE_EXPORT = 0x10
FT_PROFILE_IMPORT = 0x11
FT_RUN_INTEGRATION = 0x12
FT_INTEGRATION_REPORT = 0x20
FT_AUTH = 0x02
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
    # returns (type, payload) or None
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


class Comm:
    def __init__(self, port, baud=115200, timeout=1.0):
        self.ser = serial.Serial(port, baud, timeout=timeout)

class TCPComm:
    def __init__(self, host, port, timeout=3.0):
        import socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))

    def send_frame(self, ft, payload=b''):
        f = build_frame(ft, payload)
        self.sock.sendall(f)

    def read_frame(self, timeout=2.0):
        import socket, time
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
                        except ValueError:
                            buf = bytearray()
                            continue
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
        except socket.timeout:
            return None
        return None
    def send_frame(self, ft, payload=b''):
        f = build_frame(ft, payload)
        self.ser.write(f)

    def read_frame(self, timeout=2.0):
        deadline = time.time() + timeout
        buf = bytearray()
        while time.time() < deadline:
            b = self.ser.read(1)
            if not b:
                continue
            buf += b
            # attempt parse only when we have at least header 4 and crc 2
            if len(buf) >= 6:
                # try to parse when FRAME_START found at pos 0
                if buf[0] != FRAME_START:
                    # strip until we find FRAME_START
                    try:
                        p = buf.index(FRAME_START)
                        buf = buf[p:]
                    except ValueError:
                        buf = bytearray()
                        continue
                if len(buf) >= 4:
                    frame_len = (buf[1] << 8) | buf[2]
                    total_len = 4 + (frame_len - 1) + 2
                    if len(buf) >= total_len:
                        candidate = bytes(buf[:total_len])
                        parsed = parse_frame(candidate)
                        if parsed:
                            return parsed
                        else:
                            # corrupted - discard first byte and continue
                            buf = buf[1:]
        return None

    def send_frame_with_ack(self, ft, payload=b'', timeout=0.5, retries=3):
        """Send a frame and wait for FT_ACK for the same origin type. Returns (ok, ack_payload_bytes)"""
        for attempt in range(retries):
            self.send_frame(ft, payload)
            start = time.time()
            while time.time() - start < timeout:
                frame = self.read_frame(timeout - (time.time() - start))
                if not frame:
                    continue
                ftype, pl = frame
                if ftype == FT_ACK and len(pl) >= 1 and pl[0] == ft:
                    # ack payload excluding the origin type byte
                    return True, pl[1:]
                elif ftype == FT_NACK and len(pl) >= 1 and pl[0] == ft:
                    return False, pl[1:]
            # retry loop
        return False, b''



def cmd_profile_export(comm: Comm, idx: int):
    ok, resp = comm.send_frame_with_ack(FT_PROFILE_EXPORT, bytes([idx]), timeout=1.0, retries=3)
    print('Profile export ACK:', ok, resp)


def cmd_profile_import(comm: Comm, idx: int):
    ok, resp = comm.send_frame_with_ack(FT_PROFILE_IMPORT, bytes([idx]), timeout=1.0, retries=3)
    print('Profile import ACK:', ok, resp)


def cmd_run_integration(comm: Comm, stream=False):
    ok, resp = comm.send_frame_with_ack(FT_RUN_INTEGRATION, bytes([1 if stream else 0]), timeout=2.0, retries=3)
    print('Run integration ACK:', ok, resp)
    # read integration report (may take longer)
    rep = comm.read_frame(30.0)
    print('Report:', rep)
    if rep and rep[0] == FT_INTEGRATION_REPORT:
        payload = rep[1]
        print('Parsed report flags:', payload[:4])
        print('Summary:', payload[4:].decode('ascii', errors='ignore').rstrip('\x00'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=False, help='Serial port such as COM3 or /dev/ttyUSB0')
    parser.add_argument('--tcp', required=False, help='TCP host:port to connect to an ESP32 transport')
    parser.add_argument('--hmac-key', required=False, help='Hex-encoded HMAC-SHA256 key to use for AUTH (timestamp+HMAC)')
    parser.add_argument('cmd', choices=['profile_export','profile_import','run_integration','hello','auth'])
    parser.add_argument('arg', nargs='?', help='Index for profiles, "stream" for run_integration, or token for auth')
    args = parser.parse_args()

    conn = None
    if args.tcp:
        host, port = args.tcp.split(':')
        conn = TCPComm(host, int(port))
    elif args.port:
        conn = Comm(args.port)
    else:
        parser.error('Either --port or --tcp must be specified')

    if args.cmd == 'profile_export':
        idx = int(args.arg) if args.arg else 0
        cmd_profile_export(conn, idx)
    elif args.cmd == 'profile_import':
        idx = int(args.arg) if args.arg else 0
        cmd_profile_import(conn, idx)
    elif args.cmd == 'run_integration':
        stream = (args.arg == 'stream')
        cmd_run_integration(conn, stream)
    elif args.cmd == 'hello':
        conn.send_frame(FT_HELLO, b'')
        r = conn.read_frame(2.0)
        print('HELLO response:', r)
    elif args.cmd == 'auth':
        # If --hmac-key provided, send timestamp + HMAC-SHA256(key, timestamp) (first 16 bytes)
        if args.hmac_key:
            # parse hex key
            key = bytes.fromhex(args.hmac_key)
            ts = int(time.time()) & 0xFFFFFFFF
            ts_bytes = struct.pack('>I', ts)
            digest = hmac.new(key, ts_bytes, hashlib.sha256).digest()
            token = ts_bytes + digest[:16]
            ok, resp = conn.send_frame_with_ack(FT_AUTH, token, timeout=2.0, retries=3)
            print('AUTH (HMAC):', ok, resp)
        else:
            token = args.arg if args.arg else ''
            ok, resp = conn.send_frame_with_ack(FT_AUTH, token.encode('utf-8'), timeout=2.0, retries=3)
            print('AUTH (plain):', ok, resp)

if __name__ == '__main__':
    main()
