#ifndef SHA256_H
#define SHA256_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

void sha256_init(void* ctx);
void sha256_update(void* ctx, const uint8_t* data, size_t len);
void sha256_final(void* ctx, uint8_t out[32]);

// Convenience API: compute SHA256 of buffer
void sha256_hash(const uint8_t* data, size_t len, uint8_t out[32]);

#ifdef __cplusplus
}
#endif

#endif // SHA256_H
