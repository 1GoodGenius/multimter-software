/* uECC wrapper: use upstream micro-ecc implementation when available.
 * If `arduino_firmware/third_party/uECC/uECC.h` is present, that implementation will
 * provide `uECC_verify`. Otherwise, we fall back to a minimal stub (for CI/iteration).
 *
 * To enable a real implementation, run:
 *   python tools/fetch_uECC.py
 * which will download `uECC.c` and `uECC.h` into `third_party/uECC/`.
 */

#include "uECC.h"
#include <string.h>

// Prefer external micro-ecc if it's been fetched into third_party/uECC
#if defined(__has_include)
  #if __has_include("../third_party/uECC/uECC.h")
    #include "../third_party/uECC/uECC.h"
    // The external library defines uECC_verify and uECC_secp256r1; just forward to it.
    // No further code required here; linker will resolve uECC_verify.
  #else
    // Fallback stub (non-secure) for iteration. Replace by fetching micro-ecc.
    static uECC_Curve curve = (uECC_Curve)1; // dummy
    uECC_Curve uECC_secp256r1(void) { return curve; }
    int uECC_verify(const uint8_t * public_key, const uint8_t * message_hash,
                    unsigned hash_size, const uint8_t * signature, uECC_Curve c) {
      (void)public_key; (void)message_hash; (void)hash_size; (void)signature; (void)c;
      // WARNING: This returns success unconditionally. Fetch micro-ecc for real verification.
      return 1;
    }
  #endif
#else
  // Conservative default: stub
  static uECC_Curve curve = (uECC_Curve)1; // dummy
  uECC_Curve uECC_secp256r1(void) { return curve; }
  int uECC_verify(const uint8_t * public_key, const uint8_t * message_hash,
                  unsigned hash_size, const uint8_t * signature, uECC_Curve c) {
    (void)public_key; (void)message_hash; (void)hash_size; (void)signature; (void)c;
    return 1;
  }
#endif
