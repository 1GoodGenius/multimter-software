#ifndef ECDSA_H
#define ECDSA_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Verify ECDSA P-256 signature
// pubkey: 64 bytes (X||Y) big-endian
// sig: 64 bytes (r||s) big-endian
// hash: 32-byte SHA256 digest
// returns true if signature verifies
int ecdsa_p256_verify(const uint8_t pubkey[64], const uint8_t sig[64], const uint8_t hash[32]);

#ifdef __cplusplus
}
#endif

#endif // ECDSA_H
