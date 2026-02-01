# Porting & Testing on Arduino UNO (ATmega328P)

This document summarizes differences, cautions, and exact changes to consider when testing the firmware on an Arduino UNO (ATmega328P) prior to verifying on the Arduino Mega.

> Important: UNO has only 2KB SRAM vs Mega's 8KB — you must reduce memory usage and features accordingly.

## Key Considerations
- SRAM limitations (2KB): dynamic allocations, large static buffers, `String` usage, and large stacks can quickly exhaust memory.
- Flash limitations: some advanced features may increase binary size; watch for linker warnings.
- Peripheral and pin differences: UNO SPI/SS pins map differently; ensure `SD_CS_PIN` and TFT pins are compatible with wiring.

## Recommended configuration changes (conservative)
- In `include/smart_oscilloscope.h`, change the defaults for UNO:
  - `#define DEFAULT_OSC_BUFFER_SIZE 128` (instead of 512)
  - `#define DEFAULT_LOG_CIRCULAR_SIZE 64` (instead of 128)
  - `#define DEFAULT_LOG_ANOMALY_SIZE 32` (instead of 64)
  - `#undef MAX_SAFE_LOG_ENTRIES` and set `#define MAX_SAFE_LOG_ENTRIES 128`

- Reduce SD streaming memory usage:
  - Lower `streamFlushThreshold` from 256 to 128 bytes.
  - Avoid using `String` for large buffers — replace with fixed `char[]` ring buffer if possible.

- Compile-time switches:
  - Add `#ifdef __AVR_ATmega328P__` blocks in `smart_oscilloscope.h` to override defaults for UNO.
  - Add `-DLOW_MEMORY_DEVICE` build define and use it to remove or limit features that use large memory.

## Feature toggles to consider disabling on UNO
- Turn off continuous SD streaming by default (or require explicit enable via `#define ENABLE_SD_STREAMING_ON_UNO`)
- Reduce UI overlays and disable heavy overlays (e.g., remove RMS/Vpp calculations or lower update frequency)
- Reduce log retention/size and number of pre/post-anomaly captures

## Suggested steps to prepare a UNO test build
1. Add compile guard in `smart_oscilloscope.h`:
```
#ifdef __AVR_ATmega328P__
  #undef DEFAULT_OSC_BUFFER_SIZE
  #define DEFAULT_OSC_BUFFER_SIZE 128
  #undef DEFAULT_LOG_CIRCULAR_SIZE
  #define DEFAULT_LOG_CIRCULAR_SIZE 64
  #undef DEFAULT_LOG_ANOMALY_SIZE
  #define DEFAULT_LOG_ANOMALY_SIZE 32
  #undef MAX_SAFE_LOG_ENTRIES
  #define MAX_SAFE_LOG_ENTRIES 128
  #define LOW_MEMORY_DEVICE
#endif
```
2. Rebuild and check link size. If memory warnings or failures occur, further reduce buffer sizes and eliminate `String` usage.
3. Run basic smoke tests (see `TESTING.md`) but avoid long-duration logging or streaming.

## Cautions / Warnings
- SD library's usage of buffers and File objects can allocate RAM — test carefully with small buffers.
- On UNO, avoid dynamic memory growth (e.g., repeated `String` concatenation) — use preallocated char arrays.
- Watch for stack overflows if ISR usage or deep recursion is added.
- Don't perform high-voltage tests on UNO without proper isolation and current limiting; UNO is used for quick functional checks only.

## Test Plan for UNO
- Start with UI-only tests (profiles, name editor, calibration wizard in blocking mode) — these require less logging/SD.
- Use `test mode` synthetic patterns instead of real inputs to avoid needing precision hardware.
- If SD is required, test with tiny buffer sizes and single-file operations (avoid streaming).

---

# END UNO_PORTING.md
