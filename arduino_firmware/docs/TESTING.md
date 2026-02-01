# Testing Guide — Smart Multimeter Firmware (Point 1)

This document details how to test the firmware features added in Point 1 (Measurement, Oscilloscope, Calculator, Data Logger, UI), automated and manual test steps, expected outputs, and troubleshooting guidance.

## 1. Prerequisites
- Hardware:
  - Arduino Mega (ATmega2560) recommended (8KB SRAM).
  - TFT ILI9341 display wired as in `smart_oscilloscope.h`.
  - Rotary encoder + push button wired to pins defined in `smart_oscilloscope.h`.
  - SD card module wired to `SD_CS_PIN` and SPI pins. Use a known-good 4GB microSD formatted FAT32.
  - Power supply for the DUT and safe test load equipment (bench PSU, current shunt, resistors, multimeter).
- Software:
  - Arduino IDE (or PlatformIO) configured for the target board (Mega 2560).
  - Serial terminal (115200 baud) for CLI interaction.
  - Host-side test capability (C++ tests in `/tests` folder): requires g++ and a Unix-like shell or Windows WSL/Cygwin.

## 2. Build & Upload
1. Open the project in Arduino IDE or PlatformIO.
2. Select `Arduino Mega 2560` as board and the correct COM port.
3. Build and upload `arduino_firmware`.
4. Open Serial Monitor @115200 baud to view logging.

## 3. Smoke Tests (first run)
- On boot you should see:
  - Initialization messages for Measurement Engine, Oscilloscope Engine, Data Logging Manager, UI Controller.
  - Info prints: Oscilloscope buffer size, Logging circular buffer size.
- Touch/encoder should not crash the MCU when actuated.

## 4. Functional Tests (manual)
Each test step includes how to exercise, expected behavior, and validation method.

### 4.1 Profiles (save/load/delete)
- Enter Profile Menu on UI (encoder short/long press as implemented).
- Create a profile: long-press on an empty slot, edit name, short-press to move cursor, long-press to save.
- Validation: Profile name should appear in list, and `PROFILE_EXPORT <idx>` CLI prints success when exported.
- Load profile: short-press list entry; device should apply calibration (verify using `CALIB_SHOW` and confirm factor values).
- Delete: open action menu -> Delete -> long-press to confirm; list should show `<empty>`.

### 4.2 Calibration Wizard
- Start wizard (Serial: `WIZ_START <range> <refV>` or UI entry) and apply known reference.
- UI shows Progress % and a final factor on completion.
- Save desired calibration via wizard 'save to profile' flow and validate with `CALIB_SHOW` and UI `showCalibrationScreen()`.
- Non-blocking: UI remains responsive during wizard progress.

### 4.3 Autorange Stability
- Use `test mode` (Serial: `T`) to toggle synthetic waveforms.
- In integration test or manual sweep, observe that autorange: performs with cooldown and hysteresis and does not rapidly toggle (chatter).
- Host tests: run `tests/test_autorange.cpp` on host to validate logic.

### 4.4 Oscilloscope Rendering & Measurements
- Waveform should draw using min/max per-pixel decimation (peaks preserved).
- Vpp and RMS values shown in lower status area; validate approximate correctness with bench measurements.

### 4.5 Trigger Detection
- Use `test mode` sine/ramp to validate rising/falling trigger detection.
- Run `RUN_INTEGRATION` and confirm triggerPassed reported in integration summary.
- Host test: `tests/test_trigger.cpp` verifies trigger logic.

### 4.6 Data Logging & SD Streaming
- Start streaming with `S` (Serial command) and verify SD file creation.
- Export logs using `E` or `exportToCSVFiltered()` for filtered export (anomalies only, time ranges).
- Trigger a threshold anomaly (e.g., set `SET_POST <n>` to a small number and generate an over-threshold measurement); verify the anomaly section is present in CSV.
- Integration test can optionally stream CSV over Serial when invoked with CSV streaming.

### 4.7 Overload Safety Indicator
- Generate an overload (simulate or apply an over-threshold voltage if safe) and verify UI shows the `OVERLOAD` banner and Serial prints. Ensure a safe external current-limiter is used when applying real signals.

## 5. Integration Test Runner
- Serial command: `RUN_INTEGRATION` executes autorange stress, trigger validation, anomaly logging, SD export, and returns a summary printed to Serial.
- To stream CSV from SD (if exported to `integration_log.csv`), run `RUN_INTEGRATION` from UI (long press) or `RUN_INTEGRATION` followed by reading the file. The integration routine will attempt to stream `integration_log.csv` over Serial if available.
- Check UI `Integration Test Report` for pass/fail marks and `lastIntegrationReport.summary` printed on-screen.

### Host-side framed protocol helper (Python) 🔌
- A small host helper is included at `arduino_firmware/tools/comm_helper.py`.
- Examples:
  - `python tools/comm_helper.py --port COM3 profile_export 1` → request that the device export profile `1` to SD and receive an ACK.
  - `python tools/comm_helper.py --port COM3 run_integration stream` → run integration test and request CSV streaming; the script will display the framed integration report.
- A small test `tools/test_comm.py` validates the frame build/parse logic locally.
- Note: the firmware supports ACK/NACK frames; the host helper will wait for ACK and can be used in automation to retry on NACK/timeouts.

### CI integration
- A helper script `tools/integration_ci.py` runs the framed `RUN_INTEGRATION` command and evaluates the `INTEGRATION_REPORT` payload; the script exits non-zero if the test reports failures. A GitHub Actions workflow `/.github/workflows/integration.yml` runs unit comm tests and (optionally) the `integration_ci.py` if a `DEVICE_PORT` secret is configured.

### Watchdog & Self-test
- Commands available over serial:
  - `SELFTEST` → runs a quick on-device self-test (EEPROM load, SD presence, basic osc buffer checks) and prints PASS/FAIL.
  - `WDT_ON` / `WDT_OFF` → enable/disable the hardware watchdog (AVR only). Use with caution during development.

### UNO/low-memory caution (summary)
- On UNO, streaming to SD is disabled by default to avoid OOM; use smaller buffers and enable only when required.

## 6. Host Tests (unit-ish tests)
- Location: `/tests`.
- Run on host via a simple g++ compilation or provided script (if present):
  - Example: `g++ tests/test_calibration.cpp -o test_calib && ./test_calib`
  - Run `test_autorange`, `test_trigger`, `test_calibration`, `test_calculator` to validate logic independent of hardware.

## 7. Memory & Stability Checks
- Monitor serial logs for SRAM warnings printed at boot (Osc buffer / Logging buffer size warnings).
- Use local debug prints to estimate free SRAM if needed (add `FreeMemory` utility) before enabling streaming or large buffers.

## 8. Troubleshooting
- If display is blank: check SPI pins and CS/DC wiring, and confirm `TFT_CS_PIN`, `TFT_DC_PIN` match wiring.
- If SD writes fail: ensure the SD card is formatted FAT32 and `SD_CS_PIN` wiring and pullups are correct.
- If UI becomes sluggish: reduce `DEFAULT_OSC_BUFFER_SIZE` and logging buffer sizes.

## 9. Regression Tests to Add (recommended)
- Add on-target integration tests: automated script that uploads firmware, toggles `test mode`, runs `RUN_INTEGRATION` and captures serial output.
- Add on-device watchdog behavior test.

---

# END TESTING.md
