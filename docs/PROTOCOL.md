# Communication Protocol (Framed)

This document describes the lightweight framed protocol used by the multimeter project. The intent is to keep frames small, deterministic, and resilient so AVR-class devices (Arduino Mega) can parse without dynamic memory pressure.

## Frame format

- Frame start: 1 byte = 0xAA
- Length: 2 bytes (big-endian) = length of TYPE + PAYLOAD
- TYPE: 1 byte (frame type)
- PAYLOAD: variable (0..N-1) bytes
- CRC16: 2 bytes (big-endian) — computed over TYPE + PAYLOAD using CRC-16-CCITT (poly 0x1021, init 0xFFFF)

Encoded example: [0xAA][LEN_H][LEN_L][TYPE][PAYLOAD...][CRC_H][CRC_L]

## Basic semantics

- All frames are acknowledged where appropriate using FT_ACK (0xF0) and FT_NACK (0xF1). The ACK/NACK payload begins with the original type for correlation.
- The transport is byte-oriented (Serial or TCP). Frame parsing should be non-blocking and tolerant of spurious bytes.

## Core frame types (current)

- FT_HELLO (0x01) — request device identity; device responds with FT_ACK with FT_HELLO as origin byte and a version string.
- FT_AUTH (0x02) — token-based authentication; payload is UTF-8 token.
- FT_PROFILE_EXPORT (0x10), FT_PROFILE_IMPORT (0x11) — small profile commands (single-byte index for simplicity).
- FT_RUN_INTEGRATION (0x12) — run device self-tests / integration tests; may request streaming of results.
- FT_INTEGRATION_REPORT (0x20) — device→host integration results frame.
- FT_FILE_TRANSFER_START (0x30) — start a chunked file upload (payload: filename len, filename, filesize, chunk_size)
- FT_FILE_TRANSFER_CHUNK (0x31) — chunk payload (chunk_index(4 bytes BE) + data)
- FT_FILE_TRANSFER_END (0x32) — end-of-file notification (can contain checksum or final metadata)
- FT_FILE_TRANSFER_ACK (0x33) — positive ack for file transfer ops
- FT_FILE_TRANSFER_NACK (0x34) — negative ack
- FT_ESP_SELFTEST (0x35) — ESP32 transport self-test frame
- FT_ACK (0xF0) / FT_NACK (0xF1) — generic ack/nack framing with origin type byte followed by optional payload

> Note: Frame type values may change during protocol evolution; versioning should be added to the HELLO response for compatibility checks.

## File transfer flow (upload from host to device)

1. Host sends FT_FILE_TRANSFER_START with payload:
   - filename length (1 byte)
   - filename (UTF-8)
   - filesize (8 bytes, big-endian unsigned)
   - chunk_size (2 bytes, big-endian unsigned)

2. Device responds with FT_FILE_TRANSFER_ACK (payload begins with FT_FILE_TRANSFER_START, optional accept flags), or FT_FILE_TRANSFER_NACK on error.

3. Host sends chunks sequentially:
   - FT_FILE_TRANSFER_CHUNK payload: chunk_index (4 bytes BE) + data (<= chunk_size)
   - Device replies FT_FILE_TRANSFER_ACK with payload starting with FT_FILE_TRANSFER_CHUNK and the acknowledged chunk_index, or FT_FILE_TRANSFER_NACK for recoverable errors.
   - Host retries failed chunks with backoff.

4. After last chunk, host sends FT_FILE_TRANSFER_END (payload may contain CRC or final metadata). Device validates file and responds with FT_FILE_TRANSFER_ACK (or NACK).

5. If transfer is interrupted, the host can resume by sending FT_FILE_TRANSFER_START with the same filename and filesize; the device may return which chunks are present/acknowledged in the initial ACK payload so the host can resume by only sending missing chunks.

## Reliability considerations

- Use small chunk sizes for AVR devices (512–1024 bytes recommended).
- Acknowledge each chunk to limit RAM pressure and avoid buffering large blocks on the device.
- Include per-chunk CRC (or rely on frame-level CRC) to validate integrity.
- Keep transfer protocol extensible by adding TLV fields in start/ack payloads.

## Security

- The current AUTH frame uses a simple token; for networked deployments prefer SSH tunnels or TLS.
- Do not enable remote flashing or writeable file transfer without stronger authentication and signed payloads.

## Examples

- HELLO
  - Host: [0xAA][0x00][0x01][0x01][CRC]
  - Device: [FT_ACK][0x01]['FWv1.1-Point2']

- Start transfer (example):
  - Host sends FT_FILE_TRANSFER_START with filename "firmware.bin" and chunk_size 1024.
  - Device replies FT_FILE_TRANSFER_ACK indicating acceptance and a resume map or next expected chunk.

---

This is an initial protocol draft and should be kept in `docs/PROTOCOL.md`. We'll evolve it with TLV fields and message versioning for forward compatibility.