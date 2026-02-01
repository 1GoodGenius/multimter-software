# Security Hardening & OTA Updates

This document outlines recommended security enhancements for production deployments and over-the-air (OTA) firmware update procedures.

## Current State (Basic)

- Token-based AUTH with a plaintext token stored in EEPROM
- Unencrypted serial/TCP communication
- No firmware signature verification

## Recommended Enhancements

### 1. Upgrade Authentication to Token + HMAC

Status: IMPLEMENTED — HMAC-SHA256 timestamped AUTH is active. Device supports `AUTH_SETKEY` and `AUTH_MODE HMAC` to enable.

### 2. Signed Firmware (OTA) Verification

We added an OTA signed update flow:
- Host signs firmware with **ECDSA P-256** (recommended for embedded: small keys, fast verification). Host tooling `tools/sign_firmware.py` produces a 64-byte raw signature (r||s).
- Host sends firmware using the chunked file transfer, then issues an FT_FILE_TRANSFER_END frame containing the raw 64-byte signature.
- Device stores uploaded file to `pending_update.bin` on SD, computes SHA256, and verifies signature using the provisioned public key stored via `OTA_SET_PUBKEY <hex64bytes>` (128 hex chars, X||Y big-endian). If signature verifies, device sets a pending flag in EEPROM to indicate a validated update.

IMPORTANT: Current firmware includes the OTA wiring and ECDSA interface but uses a small verification stub (placeholder `uECC_verify`) to allow iteration and CI testing. The next step is to integrate a full `micro-ecc` (uECC) or comparable ECDSA verification implementation (PR incoming). Do not rely on this for production until the verification implementation is replaced and tested on hardware.

CLI commands:
- `OTA_SET_PUBKEY <hex128>` — provision the 64-byte public key (X||Y) into EEPROM.
- `OTA_CHECK` — prints pending update flag value (1 = pending).

Host helpers:
- `tools/sign_firmware.py --key privkey.pem --in firmware.bin --out firmware.sig` — create signature (r||s).
- `tools/test_signed_ota.py --port COM3 --file firmware.bin --priv privkey.pem` — sign & upload in one step.

Next steps (high priority):
- [x] Integrate full `micro-ecc` (uECC) verification (replace stub) and validate on ATmega2560 and UNO builds. **Action:** Run `python arduino_firmware/tools/fetch_uECC.py` to download the upstream sources into `arduino_firmware/third_party/uECC/`, then rebuild firmware and test.
- [x] Implement bootloader-compatible flashing flow: mark pending update and invoke bootloader to write to flash on restart, with post-flash self-test and rollback. **Action:** We added a simulation `OTA::applyPendingUpdate()` and CLI commands `OTA_APPLY`/`OTA_ROLLBACK` for testing and CI; we also added `OTA_REBOOT_APPLY` to set the pending flag and reboot to the bootloader. The bootloader should check the pending flag at EEPROM address `0x500 + 128` and, if set, apply the SD-stored `pending_update.bin` or equivalent flash image.
- [ ] Add E2E tests for invalid signatures (should be rejected) and corrupt files (CRC mismatch) — will be added after uECC fetch to run on real verification logic.

Bootloader integration guidance:
- The device sets the pending flag at EEPROM address `0x500 + 128` and then reboots (via watchdog) when `OTA_REBOOT_APPLY` is executed.
- The bootloader is expected to detect this flag at boot, move/flash the `pending_update` image into program memory, mark it as active, run basic self-tests, and clear the pending flag only when the new image passes.
- If the new image fails self checks, the bootloader should restore prior image (A/B or backup) and clear the pending flag, logging/reporting the failure.

Note: we provide simulated apply/rollback in `OTA::applyPendingUpdate()` for CI and early testing. For production, integrate these flags with your bootloader's update mechanism.

Instead of a simple token, use an HMAC-based scheme. The device supports an HMAC-SHA256 verification where the host sends a 4-byte timestamp (big-endian) followed by the first 16 bytes of HMAC-SHA256(key, timestamp).

Host example:
```python
import hmac
import hashlib
import struct

SECRET_KEY = bytes.fromhex("0011223344556677...")

ts = int(time.time()) & 0xFFFFFFFF
payload = struct.pack('>I', ts) + hmac.new(SECRET_KEY, struct.pack('>I', ts), hashlib.sha256).digest()[:16]
# send payload as FT_AUTH frame
```

Device provisioning (local serial CLI):
```
# Set key on device (hex encoded)
AUTH_SETKEY 00112233445566778899aabbccddeeff
# Enable HMAC mode
AUTH_MODE HMAC
```

Firmware side:
```cpp
// In communication_manager.cpp: internalAuthHandler
// payload: 4 bytes timestamp (BE) + 16 bytes token
// compute HMAC-SHA256(key, timestamp) and compare first 16 bytes
```

Firmware side:
```cpp
// In communication_manager.cpp: internalAuthHandler
void internalAuthHandler(const uint8_t* payload, uint16_t len) {
  if (len < 8) { /* reject */ return; }
  
  // payload: 4 bytes timestamp (BE) + 16 bytes token
  uint32_t ts = ((uint32_t)payload[0] << 24) | ... ;
  uint32_t now = millis() / 1000;  // rough timestamp
  
  if (abs(now - ts) > 300) {  // 5-minute window
    /* reject stale timestamp */
  }
  
  // Verify HMAC (requires HMAC-SHA256 library or simplify to SHA256)
  // For AVR, consider using a lightweight HMAC or move to ESP32
  // ...
  
  authOK = true;
}
```

### 2. TLS/mTLS Transport (for ESP32 WiFi bridge)

If using ESP32 as a bridge, add TLS. Set `TLS_ENABLED 1` and provide a server certificate + key in `esp32_bridge/certs.h`.

Example (server):
```cpp
#include <WiFiClientSecure.h>
WiFiServerSecure server(5000);
// server.setCertificate(TEST_CERT_PEM, TEST_PRIVKEY_PEM);
server.begin();
```

Host-side TLS client example (verify server cert):
```python
import socket, ssl
context = ssl.create_default_context(cafile='ca.pem')
# Use client cert/key when mTLS is required:
# context.load_cert_chain(certfile='client.crt', keyfile='client.key')
with socket.create_connection(('192.168.4.1', 5000)) as sock:
    with context.wrap_socket(sock, server_hostname='multimeter.local') as ssock:
        ssock.sendall(b'HELLO')
```

Mutual TLS (mTLS)

- Generate your own CA, sign server and client certificates with it, and store the CA PEM in `esp32_bridge/certs.h` as `TEST_CA_PEM`.
- Enable `MTLS_ENABLED 1` in `serial_bridge.ino`; update the ESP32 server code to load the CA into the secure server (APIs vary by core: e.g., `server.setClientCACert(TEST_CA_PEM)` or `WiFiClientSecure::setCACert(TEST_CA_PEM)`).

Quick OpenSSL example to create CA, server and client certs for testing:
```bash
# Create CA
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 365 -out ca.pem -subj '/CN=Multimeter-CA'

# Server key/cert (signed by CA)
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj '/CN=multimeter.local'
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha256

# Client key/cert (signed by CA)
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj '/CN=multimeter-client'
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out client.crt -days 365 -sha256
```

Use `client.crt` + `client.key` on the host side, and `ca.pem` on the ESP32 (in `TEST_CA_PEM`) to validate client certificates.

### 3. Signed Firmware Updates (OTA)

Before implementing OTA, sign firmware:

```bash
# On build machine
openssl dgst -sha256 -sign private_key.pem firmware.bin > firmware.sig
```

Device verifies signature before accepting:
```cpp
// Pseudo-code in FT_FILE_TRANSFER_END handler
uint8_t sig[64];  // 512-bit RSA sig
if (!verify_signature(firmware_hash, sig, public_key)) {
  sendFrameWithNack(FT_FILE_TRANSFER_END);
  return;
}
writeToFlash(firmware);
reboot();
```

### 4. SSH Tunnel for Unencrypted Protocols

For serial or unencrypted TCP, tunnel via SSH:

```bash
# On host
ssh -L 5000:localhost:5000 user@device-gateway

# Then use localhost:5000
python tools/file_transfer.py --tcp localhost:5000 --send firmware.bin
```

## OTA Update Workflow (Recommended Implementation)

### Phase 1: Preparation
1. Build firmware with version info (e.g., "v1.2-secured")
2. Generate SHA256 hash: `sha256sum firmware.bin`
3. Sign hash with private key: `openssl dgst -sha256 -sign key firmware.bin`
4. Upload both `firmware.bin` and `firmware.sig` to update server

### Phase 2: Device Check-In
Device periodically checks:
```
GET /api/update?version=v1.1&device_id=<id>
Response: { "version": "v1.2", "url": "https://...", "hash": "abc123...", "sig_url": "https://..." }
```

### Phase 3: Download & Verify
```cpp
// Download firmware and signature
// Verify: hash(firmware) and signature(hash, public_key) are valid
// If valid, flash; if invalid, retry or alert

if (!verify_signature_ok) {
  delay(10000);  // backoff
  return;  // try again later
}
```

### Phase 4: Flash & Rollback
```cpp
// Flash to secondary partition (A/B scheme)
// Reboot and test basic functionality
// If all OK, mark as primary
// If fail, restore old partition (rollback)

writeToSecondary(firmware);
reboot();

// On boot:
if (selfTestOk()) {
  markAsPrimary();
} else {
  rollbackToOld();
  alertHost();
}
```

## Recommended Order of Implementation

1. ✅ **Immediate (Already Done):**
   - Framed protocol with CRC
   - Token-based AUTH
   - File transfer with per-chunk ACK

2. **Next (Production-Ready):**
   - [x] Upgrade to HMAC+timestamp AUTH (implemented)
   - [ ] Add TLS to ESP32 bridge
   - [ ] Sign firmware with RSA/ECDSA

3. **Future (Hardened):**
   - [ ] Device certificate pairing (mutual TLS)
   - [ ] Rate-limited auth attempts
   - [ ] Encrypted EEPROM storage

## Testing & Deployment Checklist

- [ ] Unit tests for HMAC verification
- [ ] E2E test with signed firmware
- [ ] Test rollback on corrupted firmware
- [ ] Validate TLS handshake under poor network conditions
- [ ] Document key storage and rotation
- [ ] Test OTA timeout recovery
- [ ] Verify signature check can't be bypassed

---

See `docs/PROTOCOL.md` for frame format and `tools/file_transfer.py` for implementation reference.
