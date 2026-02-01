#include "ecdsa.h"
#include "sha256.h"
#include <string.h>

// Minimal wrapper around micro-ecc (uECC) library for P-256 ECDSA verification.
// For brevity and portability we include a subset of uECC code here. This is intended
// for verification only (no signing on-device).

// NOTE: In constrained devices this implementation must be tested for flash and RAM usage.
// If resource limits are tight, consider performing verification on the ESP32 bridge.

// Include uECC implementation (small subset). For production, replace with upstream micro-ecc.

// We provide a thin verify implementation - this is a placeholder that calls into uECC.
// Because embedding full uECC here would be long, we'll import a single-file implementation.

#include "uECC.h"

int ecdsa_p256_verify(const uint8_t pubkey[64], const uint8_t sig[64], const uint8_t hash[32]) {
  // uECC_verify expects public key in compressed/uncompressed X||Y format and signature r||s
  return uECC_verify(pubkey, hash, 32, sig, uECC_secp256r1());
}
