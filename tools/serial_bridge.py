#!/usr/bin/env python3
"""Simple serial-to-TCP bridge example.

Usage: python tools/serial_bridge.py --serial /dev/ttyACM0 --baud 115200 --tcp-port 5000

This is intentionally small and robust: handles one TCP client at a time, reconnects serial port if it disappears.
"""

import argparse
import logging
import socket
import sys
import threading
import time

try:
    import serial
except Exception:
    print("Please install pyserial: pip install pyserial")
    sys.exit(1)

logger = logging.getLogger("serial_bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def tcp_client_handler(client_sock, ser):
    """Forward bytes in both directions between client_sock and ser."""
    logger.info("Client connected: %s", client_sock.getpeername())

    def from_tcp():
        try:
            while True:
                data = client_sock.recv(4096)
                if not data:
                    break
                ser.write(data)
        except Exception as e:
            logger.debug("TCP->Serial exception: %s", e)
        finally:
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass

    def from_serial():
        try:
            while True:
                data = ser.read(ser.in_waiting or 1)
                if data:
                    client_sock.sendall(data)
        except Exception as e:
            logger.debug("Serial->TCP exception: %s", e)
        finally:
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass

    t1 = threading.Thread(target=from_tcp, daemon=True)
    t2 = threading.Thread(target=from_serial, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    client_sock.close()
    logger.info("Client disconnected")


def run_bridge(serial_port, baudrate, tcp_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", tcp_port))
    server.listen(1)
    logger.info("Listening on TCP port %d, bridging to serial %s@%d", tcp_port, serial_port, baudrate)

    ser = None
    try:
        while True:
            if ser is None or not ser.is_open:
                try:
                    ser = serial.Serial(serial_port, baudrate, timeout=0)
                    logger.info("Opened serial port %s", serial_port)
                except Exception as e:
                    logger.warning("Failed to open serial port %s: %s", serial_port, e)
                    time.sleep(2)
                    continue

            try:
                client_sock, _ = server.accept()
            except KeyboardInterrupt:
                break

            # Only one client at a time
            try:
                tcp_client_handler(client_sock, ser)
            except Exception as e:
                logger.warning("Client handler error: %s", e)

    finally:
        try:
            server.close()
        except Exception:
            pass
        try:
            if ser:
                ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--serial", required=True, help="Serial device (e.g., COM3 or /dev/ttyACM0)")
    p.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    p.add_argument("--tcp-port", type=int, default=5000, help="TCP port to listen on")
    args = p.parse_args()
    run_bridge(args.serial, args.baud, args.tcp_port)
