# ESP32 Wi‑Fi Transport Backend

This document explains how to use the ESP32 transport implemented in the firmware's `communication_manager` as a Wi‑Fi TCP server.

Modes of use

- ESP32 as *transport bridge* connected to Arduino Mega via Serial:
  - Run a small bridge firmware on ESP32 that forwards TCP frames to the Mega over Serial and vice versa.
  - Advantages: keep measurement code on Mega; add Wi‑Fi without porting the entire stack.

- ESP32 as *full device* (future port):
  - Port measurement drivers to ESP32 and run the full firmware on ESP32 (requires ADC/display driver porting).
  - Advantages: native Wi‑Fi, more RAM, full network features.

How to use the built-in transport (firmware side)

- `Comm::useESP32Transport(ssid, pass, port)` will configure a Soft-AP and open a TCP server on `port`.
- The `ESP32Transport` listens for a single client and relays framed messages to `Comm::poll()`.
- Frame format remains: `[0xAA][LEN_HIGH][LEN_LOW][TYPE][PAYLOAD...][CRC16]`.

Testing

- On the host, you can use `tools/comm_helper.py --tcp <esp_ip>:<port>` to connect directly and send frames.
- A `HELLO` / `AUTH` handshake is available for basic pairing/security:
  - Send `HELLO` frame (FT_HELLO) to get device version.
  - Send `AUTH` (FT_AUTH) with a pre-shared token to authenticate; the device will reply ACK/NACK.

Security

- The transport currently supports a simple token-based AUTH. For production, add secure pairing and encryption (TLS) and implement signed firmware updates.

Implementation notes

- The ESP32 transport implementation (`src/transport_esp32.cpp`) is guarded by `#if defined(ESP32)` and will not affect Arduino Mega builds.
- Consider adding an option to operate ESP32 in STA mode (connect to existing AP) instead of Soft-AP.

