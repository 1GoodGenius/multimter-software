#ifndef HMAC_H
#define HMAC_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// HMAC-SHA256: key up to 64 bytes, output 32 bytes
void hmac_sha256(const uint8_t* key, size_t keylen, const uint8_t* data, size_t datalen, uint8_t out[32]);

#ifdef __cplusplus
}
#endif

#endif // HMAC_H
