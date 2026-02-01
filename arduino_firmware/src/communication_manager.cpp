#include "communication_manager.h"
#include <Arduino.h>
#include <vector>

namespace {
static const uint8_t FRAME_START = 0xAA;

// Simple receive state
enum RxState { WAIT_START, READ_LEN1, READ_LEN2, READ_TYPE, READ_PAYLOAD, READ_CRC1, READ_CRC2 };

struct RxContext {
  RxState state = WAIT_START;
  uint16_t len = 0;
  uint16_t read = 0;
  uint8_t type = 0;
  std::vector<uint8_t> buffer;
  uint8_t crc_h = 0, crc_l = 0;
} rx;

// Handler table
FrameHandler handlers[256] = {0};

// ACK tracking for sendFrameWithAck
volatile bool ackReceived = false;
uint8_t ackOriginType = 0; // original frame type that was acked
std::vector<uint8_t> ackPayload;

// Active transport (defaults to serial transport below)
Transport* activeTransport = nullptr;

uint16_t calc_crc16(const uint8_t* data, uint16_t len) {
  uint16_t crc = 0xFFFF;
  for (uint16_t i = 0; i < len; ++i) {
    crc ^= (uint16_t)data[i] << 8;
    for (uint8_t j = 0; j < 8; ++j) {
      if (crc & 0x8000) crc = (crc << 1) ^ 0x1021;
      else crc <<= 1;
    }
  }
  return crc;
}

// Internal handler for ACK frames
void internalAckHandler(const uint8_t* payload, uint16_t len) {
  if (len < 1) return;
  ackOriginType = payload[0];
  ackPayload.clear();
  if (len > 1) ackPayload.insert(ackPayload.end(), payload + 1, payload + len);
  ackReceived = true;
}

// Authentication state and token
static String expectedAuthToken = String("multimeter-default-token");
static bool authOK = false;

// HMAC auth state
#include <EEPROM.h>
#include "hmac.h"
static bool hmacEnabled = false;
static uint8_t hmacKey[64]; // up to 64 bytes
static uint8_t hmacKeyLen = 0;

// EEPROM layout for auth key
#define EEPROM_AUTH_MAGIC_ADDR 0x400
#define EEPROM_AUTH_MAGIC 0xA5A5A5A5
#define EEPROM_AUTH_KEY_LEN_ADDR (EEPROM_AUTH_MAGIC_ADDR + 4)
#define EEPROM_AUTH_KEY_ADDR (EEPROM_AUTH_KEY_LEN_ADDR + 1)


// HELLO handler: return version string in ACK payload
void internalHelloHandler(const uint8_t* payload, uint16_t len) {
  const char* ver = "FWv1.1-Point2";
  uint8_t resp[64];
  resp[0] = FT_HELLO;
  size_t l = strlen(ver);
  if (l > sizeof(resp)-1) l = sizeof(resp)-1;
  memcpy(&resp[1], ver, l);
  Comm::sendFrame(FT_ACK, resp, (uint16_t)(1 + l));
}

// AUTH handler: supports either plaintext token (legacy) or HMAC(timestamp) when HMAC enabled
void internalAuthHandler(const uint8_t* payload, uint16_t len) {
  // Legacy plaintext token: echo behavior when not using HMAC
  if (!isHmacEnabled()) {
    if (len == 0) { uint8_t r = FT_AUTH; Comm::sendFrame(FT_NACK, &r, 1); return; }
    String t = String((const char*)payload, len);
    if (t == expectedAuthToken) {
      authOK = true;
      uint8_t resp[2] = { FT_AUTH, 1 };
      Comm::sendFrame(FT_ACK, resp, 2);
    } else {
      uint8_t resp[2] = { FT_AUTH, 0 };
      Comm::sendFrame(FT_NACK, resp, 2);
    }
    return;
  }

  // HMAC flow: payload: 4 bytes timestamp (BE) + 16 or 32 bytes HMAC
  if (len < 4 + 16) { uint8_t r = FT_AUTH; Comm::sendFrame(FT_NACK, &r, 1); return; }
  uint32_t ts = ((uint32_t)payload[0] << 24) | ((uint32_t)payload[1] << 16) | ((uint32_t)payload[2] << 8) | ((uint32_t)payload[3]);
  uint8_t sig_len = (uint8_t)(len - 4);
  const uint8_t* sig = payload + 4;

  // Check timestamp for freshness (allow +/- 300 seconds)
  uint32_t now = (uint32_t)(millis() / 1000);
  uint32_t window = 300; // 5 minutes
  if (ts > now + window || now > ts + window) {
    uint8_t resp[2] = { FT_AUTH, 0 };
    Comm::sendFrame(FT_NACK, resp, 2);
    return;
  }

  // Compute HMAC-SHA256 over the 4-byte timestamp (big-endian)
  uint8_t computed[32];
  hmac_sha256(hmacKey, hmacKeyLen, payload, 4, computed);

  // Compare either 16-byte truncated or full 32 bytes
  bool ok = false;
  if (sig_len == 16) {
    ok = true;
    for (uint8_t i = 0; i < 16; ++i) if (computed[i] != sig[i]) { ok = false; break; }
  } else if (sig_len == 32) {
    ok = true;
    for (uint8_t i = 0; i < 32; ++i) if (computed[i] != sig[i]) { ok = false; break; }
  } else {
    ok = false;
  }

  if (ok) {
    authOK = true;
    uint8_t resp[2] = { FT_AUTH, 1 };
    Comm::sendFrame(FT_ACK, resp, 2);
  } else {
    uint8_t resp[2] = { FT_AUTH, 0 };
    Comm::sendFrame(FT_NACK, resp, 2);
  }
}

// OTA state for signed updates
#ifdef FILE_TRANSFER_ENABLED
#include <SD.h>
static bool otaReceiving = false;
static uint32_t otaExpectedSize = 0;
static uint32_t otaBytesReceived = 0;
static uint8_t otaFileType = 0;
static File otaFile;
// Public key storage (P-256 X||Y 64 bytes)
#define EEPROM_OTA_PUBKEY_ADDR 0x500
static uint8_t otaPubKey[64];
static uint8_t otaPubKeyLen = 0;
static uint8_t otaSignature[64];
static uint8_t otaSignatureLen = 0;
#endif

// File transfer handler stubs
void internalFileStartHandler(const uint8_t* payload, uint16_t len) {
#ifdef FILE_TRANSFER_ENABLED
  // Payload: 4 bytes file_size (BE), 1 byte file_type
  if (len < 5) { uint8_t resp[1] = { FT_FILE_TRANSFER_START }; Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1); return; }
  otaExpectedSize = ((uint32_t)payload[0] << 24) | ((uint32_t)payload[1] << 16) | ((uint32_t)payload[2] << 8) | ((uint32_t)payload[3]);
  otaFileType = payload[4];
  otaBytesReceived = 0;
  // Try to open SD file for writing
  if (!SD.begin()) {
    uint8_t resp[1] = { FT_FILE_TRANSFER_START };
    Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1);
    return;
  }
  otaFile = SD.open("pending_update.bin", FILE_WRITE);
  if (!otaFile) { uint8_t resp[1] = { FT_FILE_TRANSFER_START }; Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1); return; }
  otaReceiving = true;
  uint8_t resp[2] = { FT_FILE_TRANSFER_START, 1 };
  Comm::sendFrame(FT_FILE_TRANSFER_ACK, resp, 2);
#else
  uint8_t resp[1] = { FT_FILE_TRANSFER_START };
  Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1);
#endif
}

void internalFileChunkHandler(const uint8_t* payload, uint16_t len) {
#ifdef FILE_TRANSFER_ENABLED
  if (!otaReceiving) { uint8_t resp[1] = { FT_FILE_TRANSFER_CHUNK }; Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1); return; }
  // Payload: 4-byte chunk index, followed by chunk bytes
  if (len < 4) { uint8_t resp[1] = { FT_FILE_TRANSFER_CHUNK }; Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1); return; }
  uint32_t idx = ((uint32_t)payload[0] << 24) | ((uint32_t)payload[1] << 16) | ((uint32_t)payload[2] << 8) | ((uint32_t)payload[3]);
  const uint8_t* chunk = payload + 4;
  uint16_t chunklen = len - 4;
  // Append chunk to file (we assume chunks are sent in order)
  size_t w = otaFile.write(chunk, chunklen);
  otaBytesReceived += w;
  // Acknowledge chunk
  uint8_t resp[5];
  resp[0] = FT_FILE_TRANSFER_CHUNK;
  resp[1] = (uint8_t)(idx >> 24);
  resp[2] = (uint8_t)(idx >> 16);
  resp[3] = (uint8_t)(idx >> 8);
  resp[4] = (uint8_t)(idx & 0xFF);
  Comm::sendFrame(FT_FILE_TRANSFER_ACK, resp, 5);
#else
  uint8_t resp[1] = { FT_FILE_TRANSFER_CHUNK };
  Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1);
#endif
}

void internalFileEndHandler(const uint8_t* payload, uint16_t len) {
#ifdef FILE_TRANSFER_ENABLED
  if (!otaReceiving) { uint8_t resp[1] = { FT_FILE_TRANSFER_END }; Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1); return; }
  // Payload: signature bytes (64 bytes expected for P-256 r||s) -- may include optional metadata after
  if (len < 64) { uint8_t resp[1] = { FT_FILE_TRANSFER_END }; Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1); return; }
  otaFile.flush();
  otaFile.close();
  // Read signature
  otaSignatureLen = 64;
  memcpy(otaSignature, payload, otaSignatureLen);
  // Compute SHA256 of file stored at pending_update.bin
  File f = SD.open("pending_update.bin", FILE_READ);
  if (!f) { uint8_t resp[1] = { FT_FILE_TRANSFER_END }; Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1); otaReceiving = false; return; }
  // compute hash in streaming fashion
  uint8_t hbuf[32];
  sha256_ctx_t ctx; // use a small ctx type in sha256 implementation
  sha256_init(&ctx);
  const size_t BUF_SZ = 256;
  uint8_t buf[BUF_SZ];
  while (f.available()) {
    size_t r = f.read(buf, BUF_SZ);
    sha256_update(&ctx, buf, r);
  }
  sha256_final(&ctx, hbuf);
  f.close();

  // Load public key from EEPROM
  uint8_t pkmagic = EEPROM.read(EEPROM_OTA_PUBKEY_ADDR);
  if (pkmagic != 0xA5) {
    // No public key provisioned
    uint8_t resp[2] = { FT_FILE_TRANSFER_END, 2 };
    Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 2);
    otaReceiving = false;
    return;
  }
  for (uint8_t i = 0; i < 64; ++i) otaPubKey[i] = EEPROM.read(EEPROM_OTA_PUBKEY_ADDR + 1 + i);
  otaPubKeyLen = 64;

  // Verify signature
  int ok = ecdsa_p256_verify(otaPubKey, otaSignature, hbuf);
  if (!ok) {
    uint8_t resp[2] = { FT_FILE_TRANSFER_END, 0 };
    Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 2);
    otaReceiving = false;
    return;
  }

  // Signature OK. Persist a flag that indicates pending update is ready.
  EEPROM.write(EEPROM_OTA_PUBKEY_ADDR + 128, 1); // pending flag
  uint8_t resp[2] = { FT_FILE_TRANSFER_END, 1 };
  Comm::sendFrame(FT_FILE_TRANSFER_ACK, resp, 2);

  // Optionally trigger a reboot into bootloader to apply update (implementation dependent)
  otaReceiving = false;
#else
  uint8_t resp[1] = { FT_FILE_TRANSFER_END };
  Comm::sendFrame(FT_FILE_TRANSFER_NACK, resp, 1);
#endif
}

#ifdef ESP32
bool esp32SelfTest(const char* ssid, const char* pass, uint16_t port) {
  bool ok = useESP32Transport(ssid, pass, port);
  uint8_t resp[2] = { FT_ESP_SELFTEST, ok ? 1 : 0 };
  Comm::sendFrame(FT_ACK, resp, 2);
  return ok;
}
#endif

// --- SerialTransport (default) ---
class SerialTransport : public Transport {
public:
  void begin(unsigned long baud = 115200) override { Serial.begin(baud); }
  void poll() override { /* nothing extra */ }
  int available() override { return Serial.available(); }
  int read() override { int v = Serial.read(); return v == -1 ? -1 : v; }
  int peek() override { int v = Serial.peek(); return v == -1 ? -1 : v; }
  size_t write(const uint8_t* buf, size_t len) override { return Serial.write(buf, len); }
};

static SerialTransport serialTransport;

} // anonymous

namespace Comm {

void begin(unsigned long baud) {
  // Default transport: Serial
  activeTransport = &serialTransport;
  activeTransport->begin(baud);
  // register internal ACK handler
  registerHandler(FT_ACK, internalAckHandler);
  // register HELLO and AUTH handlers
  registerHandler(FT_HELLO, internalHelloHandler);
  registerHandler(FT_AUTH, internalAuthHandler);
  // file transfer handlers (stubs)
  registerHandler(FT_FILE_TRANSFER_START, internalFileStartHandler);
  registerHandler(FT_FILE_TRANSFER_CHUNK, internalFileChunkHandler);
  registerHandler(FT_FILE_TRANSFER_END, internalFileEndHandler);

  // Load HMAC key from EEPROM if present
  uint32_t magic = 0;
  magic |= (uint32_t)EEPROM.read(EEPROM_AUTH_MAGIC_ADDR) << 24;
  magic |= (uint32_t)EEPROM.read(EEPROM_AUTH_MAGIC_ADDR + 1) << 16;
  magic |= (uint32_t)EEPROM.read(EEPROM_AUTH_MAGIC_ADDR + 2) << 8;
  magic |= (uint32_t)EEPROM.read(EEPROM_AUTH_MAGIC_ADDR + 3);
  if (magic == EEPROM_AUTH_MAGIC) {
    uint8_t len = EEPROM.read(EEPROM_AUTH_KEY_LEN_ADDR);
    if (len > 0 && len <= 64) {
      hmacKeyLen = len;
      for (uint8_t i = 0; i < hmacKeyLen; ++i) hmacKey[i] = EEPROM.read(EEPROM_AUTH_KEY_ADDR + i);
      hmacEnabled = true;
    }
  }
}
#ifdef ESP32
// Forward declare the ESP32Transport type defined in transport_esp32.cpp
class ESP32Transport;

bool useESP32Transport(const char* ssid, const char* pass, uint16_t port) {
  // Create static instance (keeps storage in BSS)
  static ESP32Transport esp;
  bool ok = esp.beginAP(ssid, pass, port);
  if (!ok) return false;
  activeTransport = &esp;
  return true;
}
#endif
void poll() {
  // Non-intrusive: only read bytes when a frame start is present or a frame is already in progress.
  if (!activeTransport) return;
  activeTransport->poll();
  while (activeTransport->available()) {
    // If we're waiting for a start marker and the next byte isn't it, don't consume the byte so legacy ASCII CLI still works.
    if (rx.state == WAIT_START) {
      int p = activeTransport->peek();
      if (p != FRAME_START) break;
    }
    int rb = activeTransport->read();
    if (rb < 0) break;
    uint8_t b = (uint8_t)rb;
    switch (rx.state) {
      case WAIT_START:
        if (b == FRAME_START) rx.state = READ_LEN1;
        break;
      case READ_LEN1:
        rx.len = (uint16_t)b << 8;
        rx.state = READ_LEN2;
        break;
      case READ_LEN2:
        rx.len |= b;
        if (rx.len == 0) { rx.state = WAIT_START; break; }
        rx.state = READ_TYPE;
        break;
      case READ_TYPE:
        rx.type = b;
        rx.buffer.clear();
        rx.buffer.reserve(rx.len - 1);
        rx.read = 0;
        if (rx.len > 1) rx.state = READ_PAYLOAD;
        else rx.state = READ_CRC1;
        break;
      case READ_PAYLOAD:
        rx.buffer.push_back(b);
        if (++rx.read >= rx.len - 1) rx.state = READ_CRC1;
        break;
      case READ_CRC1:
        rx.crc_h = b;
        rx.state = READ_CRC2;
        break;
      case READ_CRC2: {
        rx.crc_l = b;
        uint16_t crc_in = ((uint16_t)rx.crc_h << 8) | rx.crc_l;
        // compute CRC on type + payload
        std::vector<uint8_t> tmp;
        tmp.reserve(rx.len);
        tmp.push_back(rx.type);
        tmp.insert(tmp.end(), rx.buffer.begin(), rx.buffer.end());
        uint16_t calc = calc_crc16(tmp.data(), tmp.size());
        if (calc == crc_in) {
          if (handlers[rx.type]) handlers[rx.type](rx.buffer.data(), (uint16_t)rx.buffer.size());
        } else {
          // CRC mismatch: ignore
        }
        rx.state = WAIT_START;
        break; }
    }
  }
}

bool sendFrame(uint8_t type, const uint8_t* payload, uint16_t len) {
  if (!activeTransport) return false;
  uint16_t frameLen = len + 1; // type+payload
  uint8_t header[4];
  header[0] = FRAME_START;
  header[1] = (uint8_t)(frameLen >> 8);
  header[2] = (uint8_t)(frameLen & 0xFF);
  header[3] = type;
  activeTransport->write(header, 4);
  if (len) activeTransport->write(payload, len);
  // crc on type+payload
  std::vector<uint8_t> tmp;
  tmp.reserve(frameLen);
  tmp.push_back(type);
  for (uint16_t i = 0; i < len; ++i) tmp.push_back(payload[i]);
  uint16_t crc = calc_crc16(tmp.data(), tmp.size());
  uint8_t crcBytes[2] = { (uint8_t)(crc >> 8), (uint8_t)(crc & 0xFF) };
  activeTransport->write(crcBytes, 2);
  return true;
}

size_t _writeRawTransport(const uint8_t* buf, size_t len) {
  if (!activeTransport) return 0;
  return activeTransport->write(buf, len);
}

bool sendFrameWithAck(uint8_t type, const uint8_t* payload, uint16_t len, uint16_t timeoutMs, uint8_t retries, uint8_t* out_resp, uint16_t* out_len) {
  for (uint8_t attempt = 0; attempt < retries; ++attempt) {
    // clear ack state
    ackReceived = false;
    ackPayload.clear();
    ackOriginType = 0;

    // send
    sendFrame(type, payload, len);

    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
      // allow incoming frames to be processed
      poll();
      if (ackReceived && ackOriginType == type) {
        if (out_resp && out_len) {
          *out_len = (uint16_t)ackPayload.size();
          // copy up to out_len bytes
          uint16_t copylen = min(*out_len, (uint16_t)64);
          for (uint16_t i = 0; i < copylen; ++i) out_resp[i] = ackPayload[i];
        }
        return true;
      }
      delay(5);
    }
    // retry
  }
  return false;
}
bool sendFrameWithAck(uint8_t type, const uint8_t* payload, uint16_t len, uint16_t timeoutMs, uint8_t retries, uint8_t* out_resp, uint16_t* out_len) {
  for (uint8_t attempt = 0; attempt < retries; ++attempt) {
    // clear ack state
    ackReceived = false;
    ackPayload.clear();
    ackOriginType = 0;

    // send
    sendFrame(type, payload, len);

    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
      // allow incoming frames to be processed
      poll();
      if (ackReceived && ackOriginType == type) {
        if (out_resp && out_len) {
          *out_len = (uint16_t)ackPayload.size();
          // copy up to out_len bytes
          uint16_t copylen = min(*out_len, (uint16_t)64);
          for (uint16_t i = 0; i < copylen; ++i) out_resp[i] = ackPayload[i];
        }
        return true;
      }
      delay(5);
    }
    // retry
  }
  return false;
}

void registerHandler(uint8_t type, FrameHandler handler) {
  handlers[type] = handler;
}

uint16_t crc16(const uint8_t* data, uint16_t len) {
  return calc_crc16(data, len);
}

// Set HMAC key in-memory and persist to EEPROM
void setHmacKey(const uint8_t* key, uint8_t len) {
  if (!key || len == 0 || len > 64) return;
  hmacKeyLen = len;
  for (uint8_t i = 0; i < hmacKeyLen; ++i) hmacKey[i] = key[i];
  // persist
  uint32_t magic = EEPROM_AUTH_MAGIC;
  EEPROM.write(EEPROM_AUTH_MAGIC_ADDR + 0, (uint8_t)(magic >> 24));
  EEPROM.write(EEPROM_AUTH_MAGIC_ADDR + 1, (uint8_t)(magic >> 16));
  EEPROM.write(EEPROM_AUTH_MAGIC_ADDR + 2, (uint8_t)(magic >> 8));
  EEPROM.write(EEPROM_AUTH_MAGIC_ADDR + 3, (uint8_t)(magic & 0xFF));
  EEPROM.write(EEPROM_AUTH_KEY_LEN_ADDR, hmacKeyLen);
  for (uint8_t i = 0; i < hmacKeyLen; ++i) EEPROM.write(EEPROM_AUTH_KEY_ADDR + i, hmacKey[i]);
  hmacEnabled = true;
}

// Hex string helper: expects ASCII hex with even length up to 128 chars (64 bytes)
bool setHmacKeyFromHex(const char* hex) {
  if (!hex) return false;
  uint8_t len = 0;
  // compute length
  const char* p = hex;
  while (*p) { ++p; ++len; }
  if (len % 2 != 0) return false;
  uint8_t byte_len = len / 2;
  if (byte_len == 0 || byte_len > 64) return false;
  uint8_t tmp[64];
  for (uint8_t i = 0; i < byte_len; ++i) {
    char hi = hex[i*2];
    char lo = hex[i*2+1];
    auto val = [](char c)->int { if (c >= '0' && c <= '9') return c - '0'; if (c >= 'a' && c <= 'f') return c - 'a' + 10; if (c >= 'A' && c <= 'F') return c - 'A' + 10; return -1; };
    int vhi = val(hi);
    int vlo = val(lo);
    if (vhi < 0 || vlo < 0) return false;
    tmp[i] = (uint8_t)((vhi << 4) | vlo);
  }
  setHmacKey(tmp, byte_len);
  return true;
}

void enableHmac(bool enabled) {
  hmacEnabled = enabled;
}

bool isHmacEnabled() {
  return hmacEnabled;
}

void setAuthToken(const char* token) {
  expectedAuthToken = String(token);
}

bool isAuthenticated() {
  return authOK;
}

} // namespace Comm
