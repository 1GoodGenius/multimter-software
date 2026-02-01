#ifndef COMMUNICATION_MANAGER_H
#define COMMUNICATION_MANAGER_H

#include <stdint.h>

// Lightweight framed protocol support for serial/USB and future transport layers.
// Frame format (simple): [0xAA][LEN_HIGH][LEN_LOW][TYPE][PAYLOAD...][CRC16]
// - 0xAA : Frame start
// - LEN  : length of TYPE+PAYLOAD
// - TYPE : frame type byte
// - PAYLOAD: variable
// - CRC16 : CRC over TYPE+PAYLOAD (big-endian)

// Shared frame type constants
#define FT_HELLO 0x01
#define FT_AUTH 0x02
#define FT_PROFILE_EXPORT 0x10
#define FT_PROFILE_IMPORT 0x11
#define FT_RUN_INTEGRATION 0x12
#define FT_WIZ_START 0x13
// File transfer frames (chunked, resumable)
#define FT_FILE_TRANSFER_START 0x30
#define FT_FILE_TRANSFER_CHUNK 0x31
#define FT_FILE_TRANSFER_END 0x32
#define FT_FILE_TRANSFER_ACK 0x33
#define FT_FILE_TRANSFER_NACK 0x34
#define FT_ESP_SELFTEST 0x35
#define FT_INTEGRATION_REPORT 0x20
#define FT_ACK 0xF0
#define FT_NACK 0xF1

#include "transport.h"

namespace Comm {

void begin(unsigned long baud = 115200);
void poll(); // called frequently from main loop

// Set or override the active transport. Ownership is not transferred.
void setTransport(Transport* t);
void setAuthToken(const char* token);
bool isAuthenticated();
#ifdef ESP32
// Convenience: enable built-in ESP32 Wi‑Fi transport (AP mode) with SSID/PASS and port
bool useESP32Transport(const char* ssid = "Multimeter-AP", const char* pass = "multimeter", uint16_t port = 5555);
// Run a self-test that brings up AP and returns success
bool esp32SelfTest(const char* ssid, const char* pass, uint16_t port);
#endif

// Send a frame (blocking write). Returns true on success.
bool sendFrame(uint8_t type, const uint8_t* payload, uint16_t len);

// low-level write for transports: write raw bytes to active transport
size_t _writeRawTransport(const uint8_t* buf, size_t len);

// Send frame and wait for an ACK of the same type. Optional out_resp/out_len to retrieve ACK payload.
bool sendFrameWithAck(uint8_t type, const uint8_t* payload, uint16_t len, uint16_t timeoutMs = 500, uint8_t retries = 3, uint8_t* out_resp = nullptr, uint16_t* out_len = nullptr);

// Register a callback for received frames of a particular type.
using FrameHandler = void(*)(const uint8_t* payload, uint16_t len);
void registerHandler(uint8_t type, FrameHandler handler);

// HMAC auth API
// key length must be <= 64 bytes (sha256 block size)
void setHmacKey(const uint8_t* key, uint8_t len);
// helper to write hex key (ASCII hex) into EEPROM and load it
bool setHmacKeyFromHex(const char* hex);
void enableHmac(bool enabled);
bool isHmacEnabled();

// Utility
uint16_t crc16(const uint8_t* data, uint16_t len);

} // namespace Comm

#endif // COMMUNICATION_MANAGER_H
