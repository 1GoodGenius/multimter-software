/* Micro-ecc (uECC) minimal header subset for secp256r1 verification */
#ifndef UECC_H
#define UECC_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declaration of curve type
typedef struct uECC_Curve_t * uECC_Curve;

uECC_Curve uECC_secp256r1(void);
int uECC_verify(const uint8_t * public_key, const uint8_t * message_hash,
                unsigned hash_size, const uint8_t * signature, uECC_Curve curve);

#ifdef __cplusplus
}
#endif

#endif // UECC_H
