# Bridging the Multimeter Device ↔ Host

This document describes options for connecting an Arduino Mega-based multimeter to a host over wired or wireless links when you don't have (or don't want) an ESP32-based transport.

Options

- USB Serial (recommended for development)
  - Use the device over USB serial (e.g., COMx on Windows, /dev/ttyACMx on Linux).
  - Host tooling (scripts in `tools/`) already supports SerialTransport and `tools/comm_helper.py --serial`.

- HC-05 / Bluetooth SPP (short-range wireless)
  - Provides a serial port over Bluetooth, works like a serial cable. Low power, not encrypted by default.
  - Pair the module, open the host RFCOMM/COM port, and use existing serial tooling.

- Host Serial‑to‑TCP bridge (recommended for remote local networks)
  - Run a small program on the host (PC or Raspberry Pi) that forwards traffic between a TCP port and the serial port.
  - Tools you can use: `socat`, `ser2net`, or the included `tools/serial_bridge.py`.
  - Example `socat` command (Linux):
    socat TCP-LISTEN:5000,reuseaddr,fork /dev/ttyACM0,raw,echo=0,b115200

- ESP32 as a dedicated serial bridge (recommended for portable Wi‑Fi bridging)
  - Flash a small ESP32 sketch to act as a serial-to-TCP bridge (AP or STA), then connect to the ESP32 over TCP from the host.
  - This keeps Mega firmware unchanged; the ESP32 simply forwards bytes.
  - Example: `arduino_firmware/esp32_bridge/serial_bridge.ino` (soft-AP + TCP server). Use `tools/file_transfer.py --tcp <host:port> --send <file>` to test file uploads through the bridge.
  - TLS: the bridge includes an optional TLS mode (set `TLS_ENABLED 1` and provide a PEM `cert`/`privkey` in `esp32_bridge/certs.h`). This enables a server-side TLS endpoint to protect traffic in transit.
  - mTLS (mutual TLS): set `MTLS_ENABLED 1` in `esp32_bridge/serial_bridge.ino` and place a CA PEM into `esp32_bridge/certs.h` as `TEST_CA_PEM`. The ESP32 can then verify client certificates signed by that CA for strong mutual authentication. See `docs/SECURITY_AND_OTA.md` for certificate generation examples and verification guidance.

Security and reliability notes

Security and reliability notes

- Unencrypted TCP and classic Bluetooth are not safe for production. Prefer SSH tunneling or TLS for remote access (see `docs/AUTH_HARDENING.md`).
- Use a serial bridge that supports single-client exclusivity or a simple locking mechanism to avoid multiple hosts stomping the same serial device.
- Keep timeouts and reconnect logic on both sides so that temporary link interruptions don't deadlock the device.

When to choose what

- Development on a single machine: USB Serial.
- Short-range wireless: HC-05.
- Local network remote access: host serial bridge (Python or `socat`) or ESP32 bridge if you need Wi‑Fi without a host.
- Production deployments: ESP32 or secure host tunnel with TLS/SSH + hardened auth.
