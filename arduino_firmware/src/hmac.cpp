#include "hmac.h"
#include "sha256.h"
#include <string.h>
#include <stdlib.h>

void hmac_sha256(const uint8_t* key, size_t keylen, const uint8_t* data, size_t datalen, uint8_t out[32]) {
  uint8_t k_ipad[64];
  uint8_t k_opad[64];
  uint8_t tk[32];
  size_t i;

  if (keylen > 64) {
    // If key is longer than block size, shorten it by hashing it
    sha256_hash(key, keylen, tk);
    key = tk;
    keylen = 32;
  }

  // Prepare inner and outer pads
  memset(k_ipad, 0x36, sizeof(k_ipad));
  memset(k_opad, 0x5c, sizeof(k_opad));
  for (i = 0; i < keylen; ++i) {
    k_ipad[i] ^= key[i];
    k_opad[i] ^= key[i];
  }

  // inner hash
  uint8_t inner_hash[32];
  { // init sha
    // compute SHA256(k_ipad || data)
    sha256_init(&tk); // reuse tk struct memory as temp ctx (overloaded)
    // Note: for embedded C++ we keep it simple: call sha256_hash on concatenation buffer
  }
  // Create a temp buffer: ipad + data (only used for small messages like timestamp)
  size_t buflen = 64 + datalen;
  uint8_t* buf = (uint8_t*)malloc(buflen);
  if (!buf) {
    // out-of-memory: produce zeros
    memset(out, 0, 32);
    return;
  }
  memcpy(buf, k_ipad, 64);
  memcpy(buf + 64, data, datalen);
  sha256_hash(buf, buflen, inner_hash);

  // outer hash: SHA256(opad || inner_hash)
  memcpy(buf, k_opad, 64);
  memcpy(buf + 64, inner_hash, 32);
  sha256_hash(buf, 64 + 32, out);
  free(buf);
}
