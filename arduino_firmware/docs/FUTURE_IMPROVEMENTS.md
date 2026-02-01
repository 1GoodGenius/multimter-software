# Future Improvements Roadmap (post-Point 1)

This document lists potential improvements (short/medium/long term) prioritized for impact and feasibility.

## High Priority (Short term)
- Implement a robust Communication Manager (USB CDC + framed protocol + basic command acknowledgements and CRC) to support host tooling and automated test harnesses.
- Replace `String` streaming buffer with a fixed-size ring buffer and file writer to avoid heap fragmentation.
- Add CI for host tests and a scripted on-device integration test harness (upload, run `RUN_INTEGRATION`, capture serial output).
- Implement unit-like tests for on-device state transitions (autorange, trigger) using test-mode hooks and simulated inputs.

## Medium Priority
- Add a safety manager module with explicit hardware cutoff or relay control and persistent fault logs.
- Improve oscilloscope engine with decimation/resampling + zoom/pan with performance optimizations.
- Add measurement cursors and frequency-domain tools (FFT) for more advanced analysis.

## Long Term / Nice-to-have
- BLE/Wi-Fi companion app and cloud logging + live mirroring.
- Secure firmware update path (e.g., SD-based firmware upgrade with signature checking).
- Implement a test automation mode that can run long-duration stress tests and stream compressed logs to host.

## Notes on Technical Debt
- Replace ad-hoc CSV streaming and String usage to prevent OOM on low-memory devices.
- Centralize configuration constants in a single header for easier per-board tuning.

---

# END FUTURE_IMPROVEMENTS.md
