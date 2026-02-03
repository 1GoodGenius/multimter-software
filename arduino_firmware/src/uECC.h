#ifndef UECC_SHIM_H
#define UECC_SHIM_H

#include <stdint.h>

/* If upstream uECC header is available in third_party, include it; otherwise provide
 * a minimal shim with the few symbols we use (uECC_verify and uECC_secp256r1).
 */
#if defined(__has_include)
  #if __has_include("../third_party/uECC/uECC.h")
    #include "../third_party/uECC/uECC.h"
  #else
    /* Minimal fallback declarations (non-secure stub may be provided by src/uECC.c) */
    #ifdef __cplusplus
    extern "C" {
    #endif
    typedef const void* uECC_Curve;
    uECC_Curve uECC_secp256r1(void);
    int uECC_verify(const uint8_t * public_key, const uint8_t * message_hash,
                    unsigned hash_size, const uint8_t * signature, uECC_Curve c);
    #ifdef __cplusplus
    }
    #endif
  #endif
#else
  /* Conservative fallback: declare minimal symbols */
  #ifdef __cplusplus
  extern "C" {
  #endif
  typedef const void* uECC_Curve;
  uECC_Curve uECC_secp256r1(void);
  int uECC_verify(const uint8_t * public_key, const uint8_t * message_hash,
                  unsigned hash_size, const uint8_t * signature, uECC_Curve c);
  #ifdef __cplusplus
  }
  #endif
#endif

#endif // UECC_SHIM_H
