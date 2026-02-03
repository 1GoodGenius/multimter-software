#include <Arduino.h>
#include "smart_oscilloscope.h"
#include "engines/measurement_engine.h"
#include "engines/oscilloscope_engine.h"
#include "managers/data_logging_manager.h"
#include "managers/ota_manager.h"
#include <EEPROM.h>
#include "ui_controller.h"
#include "communication_manager.h"
#include <string.h>
#ifdef __AVR__
#include <avr/wdt.h>
#endif

// --- Global Engine Instances ---
// We create global instances of our engines so they can be accessed from anywhere in the file.
MeasurementEngine measurementEngine;
OscilloscopeEngine oscilloscopeEngine(DEFAULT_OSC_BUFFER_SIZE); // safe default for ATmega2560
DataLoggingManager dataLoggingManager(DEFAULT_LOG_CIRCULAR_SIZE, DEFAULT_LOG_ANOMALY_SIZE); // safe defaults
UIController uiController(&oscilloscopeEngine, &measurementEngine);

// Integration test control
bool integrationTestRunning = false;
bool integrationStreamRequested = false;
#include "integration_report.h"

IntegrationReport lastIntegrationReport;


// Forward handlers
void onFrameProfileExport(const uint8_t* payload, uint16_t len);
void onFrameProfileImport(const uint8_t* payload, uint16_t len);
void onFrameRunIntegration(const uint8_t* payload, uint16_t len);

// Send integration report via Comm
void sendIntegrationReportFrame() {
  uint8_t payload[64];
  size_t pos = 0;
  payload[pos++] = lastIntegrationReport.autorangePassed ? 1 : 0;
  payload[pos++] = lastIntegrationReport.triggerPassed ? 1 : 0;
  payload[pos++] = lastIntegrationReport.loggingPassed ? 1 : 0;
  payload[pos++] = lastIntegrationReport.sdExportPassed ? 1 : 0;
  // copy summary (null-terminated)
  strncpy((char*)&payload[pos], lastIntegrationReport.summary, sizeof(payload)-pos-1);
  payload[sizeof(payload)-1]=0;
  size_t total = pos + strlen((char*)&payload[pos]) + 1;
  Comm::sendFrame(FT_INTEGRATION_REPORT, payload, total);
}

// Test harness and UI flags used across loop and tests
static bool testMode = false;
static int testPattern = 0; // 0=none,1=ramp,2=sine
static unsigned long testStartTime = 0;
static unsigned long lastSampleTime = 0;

// Watchdog state
static bool wdtEnabled = false;


void runIntegrationTest(bool streamCSV) {
  Serial.println("[TEST] Integration test: autorange, trigger, anomaly logging, SD export");
  bool autorangePassed = false;
  bool triggerPassed = false;
  bool loggingPassed = false;
  bool sdExportPassed = false;

  // Reset last report
  lastIntegrationReport.autorangePassed = false;
  lastIntegrationReport.triggerPassed = false;
  lastIntegrationReport.loggingPassed = false;
  lastIntegrationReport.sdExportPassed = false;
  memset(lastIntegrationReport.summary, 0, sizeof(lastIntegrationReport.summary));

  // 1) Autorange stress simulation: sweep a simulated raw voltage and ensure setRange is exercised
  Serial.println("[TEST] Autorange simulation...");
  VoltageRange initialRange = measurementEngine.getCurrentRange();
  VoltageRange lastRange = initialRange;
  for (int i = 0; i < 500; i++) {
    float raw = (float)i / 500.0f; // 0..1
    float measured = raw * measurementEngine.getCalibrationFactor(measurementEngine.getCurrentRange());
    float high = 0.8f * measurementEngine.getCalibrationFactor(measurementEngine.getCurrentRange());
    float low = 0.1f * measurementEngine.getCalibrationFactor(measurementEngine.getCurrentRange());
    if (measured > high) {
      if (measurementEngine.getCurrentRange() < RANGE_1000V) measurementEngine.setRange((VoltageRange)(measurementEngine.getCurrentRange() + 1));
    } else if (measured < low) {
      if (measurementEngine.getCurrentRange() > RANGE_200MV) measurementEngine.setRange((VoltageRange)(measurementEngine.getCurrentRange() - 1));
    }
    if (measurementEngine.getCurrentRange() != lastRange) {
      autorangePassed = true;
      lastRange = measurementEngine.getCurrentRange();
    }
    delay(2);
  }
  Serial.print("[TEST] Autorange " ); Serial.println(autorangePassed ? "PASSED" : "FAILED");

  // 2) Trigger validation
  Serial.println("[TEST] Trigger validation...");
  oscilloscopeEngine.clearBuffer();
  oscilloscopeEngine.enableTrigger(true);
  oscilloscopeEngine.setTrigger(1.65f, TRIGGER_RISING);
  oscilloscopeEngine.startCapture();
  // feed a waveform that crosses 1.65V
  for (int i=0;i<200;i++) {
    float t = (float)i / 200.0f;
    float v = 1.65f + 0.5f * sin(2.0f * 3.14159265f * 50.0f * t);
    oscilloscopeEngine.addSample(v, micros());
    delay(1);
  }
  int validCount=0; int startIndex=0; WaveformSample* wf = oscilloscopeEngine.getWaveformData(validCount, startIndex);
  if (validCount > 0) triggerPassed = true;
  Serial.print("[TEST] Trigger " ); Serial.println(triggerPassed ? "PASSED" : "FAILED");

  // 3) Anomaly logging
  Serial.println("[TEST] Anomaly logging...");
  dataLoggingManager.clearAnomalies();
  for (int i=0;i<20;i++) {
    Measurement m; m.voltage = 1000.0f + i * 10; m.current = 0.5f; m.timestamp = millis();
    dataLoggingManager.logSample(m);
  }
  if (dataLoggingManager.getAnomalyCount() > 0) loggingPassed = true;
  Serial.print("[TEST] Logging " ); Serial.println(loggingPassed ? "PASSED" : "FAILED");

  // 4) SD Export
  Serial.println("[TEST] SD export...");
  if (dataLoggingManager.isSDCardAvailable()) {
    if (dataLoggingManager.exportToCSV("integration_log.csv")) sdExportPassed = true;
  }
  Serial.print("[TEST] SD Export " ); Serial.println(sdExportPassed ? "PASSED" : "SKIPPED/FAILED");

  // Fill last report struct
  lastIntegrationReport.autorangePassed = autorangePassed;
  lastIntegrationReport.triggerPassed = triggerPassed;
  lastIntegrationReport.loggingPassed = loggingPassed;
  lastIntegrationReport.sdExportPassed = sdExportPassed;
  snprintf(lastIntegrationReport.summary, sizeof(lastIntegrationReport.summary), "A:%d T:%d L:%d S:%d", autorangePassed, triggerPassed, loggingPassed, sdExportPassed);

  // Optionally stream CSV output over Serial for automated harnesses
  if (streamCSV) {
    Serial.println("[TEST] Streaming CSV output over Serial...");
    // Stream header
    Serial.println("timestamp_ms,voltage_V,current_A,is_anomaly");
    int actualCount = dataLoggingManager.getLogCount();
    // Iterate valid circular buffer and print samples
    int valid = 0; // compute using internal API
    // we will reuse exportToCSV logic by reading the circular buffer directly (not exposed) - as a fallback, if SD has the file, send it
    if (dataLoggingManager.isSDCardAvailable()) {
      File f = SD.open("integration_log.csv");
      if (f) {
        while (f.available()) {
          Serial.write(f.read());
        }
        f.close();
      } else {
        Serial.println("[TEST] No integration_log.csv on SD to stream");
      }
    } else {
      Serial.println("[TEST] SD not available; streaming not possible for full log");
    }
  }

  // Summary
  Serial.println("[TEST] Integration summary:");
  Serial.print("  Autorange: "); Serial.println(autorangePassed?"OK":"FAIL");
  Serial.print("  Trigger: "); Serial.println(triggerPassed?"OK":"FAIL");
  Serial.print("  Logging: "); Serial.println(loggingPassed?"OK":"FAIL");
  Serial.print("  SD Export: "); Serial.println(sdExportPassed?"OK":"FAIL/SKIP");
}


void onFrameProfileExport(const uint8_t* payload, uint16_t len) {
  if (!Comm::isAuthenticated()) { uint8_t r=0; Comm::sendFrame(FT_NACK, &r, 1); return; }
  if (len < 1) { uint8_t r=0; Comm::sendFrame(FT_NACK, &r, 1); return; }
  uint8_t idx = payload[0];
  char fname[32]; snprintf(fname, sizeof(fname), "profile_%d.csv", idx);
  bool ok = measurementEngine.exportProfileToSD(idx, fname);
  uint8_t resp[3] = { FT_PROFILE_EXPORT, idx, ok ? 1 : 0 };
  Comm::sendFrame(FT_ACK, resp, 3);
}

void onFrameProfileImport(const uint8_t* payload, uint16_t len) {
  if (!Comm::isAuthenticated()) { uint8_t r=0; Comm::sendFrame(FT_NACK, &r, 1); return; }
  if (len < 1) { uint8_t r=0; Comm::sendFrame(FT_NACK, &r, 1); return; }
  uint8_t idx = payload[0];
  char fname[32]; snprintf(fname, sizeof(fname), "profile_%d.csv", idx);
  bool ok = measurementEngine.importProfileFromSD(idx, fname);
  uint8_t resp[3] = { FT_PROFILE_IMPORT, idx, ok ? 1 : 0 };
  Comm::sendFrame(FT_ACK, resp, 3);
}

void onFrameRunIntegration(const uint8_t* payload, uint16_t len) {
  bool stream = false;
  if (len >= 1) stream = payload[0] ? true : false;
  // Send immediate ACK that we received the command
  uint8_t resp[2] = { FT_RUN_INTEGRATION, stream ? 1 : 0 };
  Comm::sendFrame(FT_ACK, resp, 2);
  // Schedule the integration test to run in main loop (non-blocking handler)
  integrationStreamRequested = stream;
  integrationTestRunning = true;
}

void onOverload(bool overloaded) {
  uiController.showOverload(overloaded);
}

void setup() {
  // Start serial communication for debugging.
  Serial.begin(115200);
  while (!Serial && millis() < 2000); // Wait for serial port to connect, with a 2-sec timeout.

  Serial.println("--- Smart Oscilloscope Initializing ---");

  // Initialize the hardware-specific components of each engine.
  measurementEngine.initialize();
  measurementEngine.loadCalibrationFromEEPROM();
  Serial.println("[OK] Measurement Engine Initialized.");
  
  oscilloscopeEngine.initialize();
  Serial.println("[OK] Oscilloscope Engine Initialized.");

  if (dataLoggingManager.initialize()) {
    Serial.println("[OK] Data Logging Manager Initialized (SD Card Found).");
  } else {
    Serial.println("[WARN] Data Logging Manager: SD Card not found.");
  }

  uiController.begin();
  Serial.println("[OK] UI Controller Initialized.");

  // Register overload callback to display warnings
  extern void onOverload(bool);
  measurementEngine.setOverloadCallback(onOverload);

  // Initialize Communication Manager (framed protocol)
  Comm::begin(115200);
  Comm::registerHandler(FT_PROFILE_EXPORT, onFrameProfileExport);
  Comm::registerHandler(FT_PROFILE_IMPORT, onFrameProfileImport);
  Comm::registerHandler(FT_RUN_INTEGRATION, onFrameRunIntegration);
  Serial.println("[OK] Communication Manager Initialized.");

  // For now, we will start capturing immediately for testing purposes.
  oscilloscopeEngine.startCapture();
  
  // Initialize OTA manager and check pending update
  OTA::begin();
  if (OTA::hasPendingUpdate()) {
    Serial.println("[OTA] Pending update detected. In simulation mode, use OTA_APPLY to apply.");
  }

  // Print buffer and memory warnings (if any)
  Serial.print("[INFO] Oscilloscope buffer size: "); Serial.println(oscilloscopeEngine.getBufferSize());
  Serial.print("[INFO] Logging circular buffer size: "); Serial.println(dataLoggingManager.getLogCount());

  Serial.println("--- Initialization Complete. Starting Capture. ---");
}

void loop() {
  // This is the main control loop for the firmware.
  static bool isCurrentlyOverloaded = false;

  // 1. Determine the sample interval based on the oscilloscope's setting.
  // The sample rate is in Hz (samples per second). We convert it to a period in microseconds.
  unsigned long sampleInterval_us = 1000000 / oscilloscopeEngine.getSampleRate();

  // 2. Check if enough time has passed to take a new sample.
  unsigned long currentTime_us = micros();
  if (currentTime_us - lastSampleTime >= sampleInterval_us) {
    lastSampleTime = currentTime_us;

    // 3. It's time to take a sample. We support hardware reads or test-mode simulated signals.
    Measurement measurement;
    if (testMode) {
      // Synthetic measurement generator for validation and automated tests
      unsigned long t = (micros() - testStartTime) / 1000; // ms
      if (testPattern == 1) {
        // Ramp: from 0 -> 1100 V over 10 seconds
        float v = (1100.0f * (t % 10000) ) / 10000.0f;
        measurement.voltage = v;
        measurement.current = 0.01f;
      } else {
        // Sine around 1V amplitude (trigger testing and small-signal zoom)
        float freq = 50.0; // 50 Hz
        float time_s = t / 1000.0f;
        float v = 1.65f + 0.5f * sin(2.0f * 3.14159265f * freq * time_s);
        measurement.voltage = v;
        measurement.current = 0.01f;
      }
      measurement.timestamp = millis();
    } else {
      // getMeasurement() bundles voltage, current, and a timestamp.
      measurement = measurementEngine.getMeasurement();
    }

    // 4. Feed the new voltage sample and its timestamp into the Oscilloscope Engine.
    oscilloscopeEngine.addSample(measurement.voltage, measurement.timestamp);

    // 5. Feed the same measurement into the Data Logging Manager.
    dataLoggingManager.logSample(measurement);

    // 6. Check for safety overload conditions.
    if (!testMode) {
      if (measurementEngine.isOverloaded()) {
        if (!isCurrentlyOverloaded) {
          Serial.println("[!! SAFETY WARNING: OVERLOAD DETECTED !!]");
          isCurrentlyOverloaded = true;
        }
      } else {
        if (isCurrentlyOverloaded) {
          Serial.println("[OK] Safety condition cleared.");
          isCurrentlyOverloaded = false;
        }
      }
    }
  }

  // Update the UI
  uiController.handleEncoder();
  uiController.handleTouch();
  uiController.update();

  // Feed watchdog if enabled
#ifdef __AVR__
  if (wdtEnabled) wdt_reset();
#endif

  // Run background test state if integrationTestRunning set (scheduled by framed comm handler)
  if (integrationTestRunning) {
    Serial.println("[TEST] Running scheduled integration test (background)...");
    runIntegrationTest(integrationStreamRequested);
    // After completion, send framed report for automated hosts
    sendIntegrationReportFrame();
    integrationTestRunning = false;
    integrationStreamRequested = false;
  }

  // Poll framed Communication Manager first (non-intrusive to ASCII CLI)
  Comm::poll();

  // Handle serial test commands and calibration (non-blocking)
  static char cmdBuf[128];
  static int cmdIdx = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdIdx > 0) {
        cmdBuf[cmdIdx] = '\0';
        // Process command
        if (strncmp(cmdBuf, "T", 1) == 0) {
          testMode = !testMode;
          if (testMode) { testStartTime = micros(); testPattern = 2; Serial.println("[TEST] Test mode enabled (sine pattern)"); }
          else Serial.println("[TEST] Test mode disabled");
        } else if (strncmp(cmdBuf, "PAT 1", 5) == 0) {
          testPattern = 1; Serial.println("[TEST] Pattern set: ramp");
        } else if (strncmp(cmdBuf, "PAT 2", 5) == 0) {
          testPattern = 2; Serial.println("[TEST] Pattern set: sine");
        } else if (strncmp(cmdBuf, "S", 1) == 0) {
          if (dataLoggingManager.isSDCardAvailable()) {
            if (dataLoggingManager.startStreaming("stream_log.csv")) Serial.println("[STREAM] Started logging to SD: stream_log.csv");
            else Serial.println("[STREAM] Failed to start streaming (SD error)");
          } else Serial.println("[STREAM] SD Card not available");
        } else if (strncmp(cmdBuf, "s", 1) == 0) {
          dataLoggingManager.stopStreaming(); Serial.println("[STREAM] Stopped streaming to SD");
        } else if (strncmp(cmdBuf, "E", 1) == 0) {
          if (dataLoggingManager.isSDCardAvailable()) {
            if (dataLoggingManager.exportToCSV("exported_log.csv")) Serial.println("[EXPORT] Exported logs to exported_log.csv");
            else Serial.println("[EXPORT] Failed to export logs.");
          } else Serial.println("[EXPORT] SD Card not available");
        }
        // Calibration commands
        else if (strncmp(cmdBuf, "CALIB_SAVE", 10) == 0) {
          if (measurementEngine.saveCalibrationToEEPROM()) Serial.println("[CALIB] Saved calibration to EEPROM"); else Serial.println("[CALIB] Save failed");
        } else if (strncmp(cmdBuf, "CALIB_LOAD", 10) == 0) {
          if (measurementEngine.loadCalibrationFromEEPROM()) Serial.println("[CALIB] Loaded calibration from EEPROM"); else Serial.println("[CALIB] No valid calibration in EEPROM");
        } else if (strncmp(cmdBuf, "CALIB_SHOW", 10) == 0) {
          measurementEngine.printCalibration(Serial);
          // Also show on UI
          float f[5]; for (int i=0;i<5;i++) f[i]=measurementEngine.getCalibrationFactor((VoltageRange)i);
          uiController.showCalibrationScreen(f,5, measurementEngine.getCalibrationFactor(RANGE_200MV) /* placeholder */, measurementEngine.readCurrent());
        } else if (strncmp(cmdBuf, "CALIB_RESET", 11) == 0) {
          measurementEngine.resetCalibration(); Serial.println("[CALIB] Reset to defaults");
        } else if (strncmp(cmdBuf, "CALIB_RANGE", 11) == 0) {
          // Format: CALIB_RANGE <range_index> <ref_voltage>
          int r = -1; float ref = 0.0;
          if (sscanf(cmdBuf + 11, "%d %f", &r, &ref) == 2) {
            if (r >= 0 && r <= 4) {
              float f = measurementEngine.calibrateRange((VoltageRange)r, ref);
              if (!isnan(f)) { Serial.print("[CALIB] Range "); Serial.print(r); Serial.print(" factor="); Serial.println(f, 6); }
              else Serial.println("[CALIB] Calibration failed (invalid measurement)");
            } else Serial.println("[CALIB] Range index must be 0..4");
          } else Serial.println("[CALIB] Usage: CALIB_RANGE <range_index 0..4> <ref_voltage>");
        } else if (strncmp(cmdBuf, "CALIB_CUR_ZERO", 14) == 0) {
          float off = measurementEngine.calibrateCurrentZero(); Serial.print("[CALIB] Current offset V="); Serial.println(off, 6);
        } else if (strncmp(cmdBuf, "CALIB_CUR", 9) == 0) {
          float known=0.0; if (sscanf(cmdBuf + 9, "%f", &known) == 1) {
            float sens = measurementEngine.calibrateCurrentKnown(known);
            if (!isnan(sens)) { Serial.print("[CALIB] Current sens V/A="); Serial.println(sens, 6); }
            else Serial.println("[CALIB] Calibration failed (bad input)");
          } else Serial.println("[CALIB] Usage: CALIB_CUR <known_current_in_amps>");
        } else if (strncmp(cmdBuf, "WIZ_START", 9) == 0) {
          int r = -1; float ref = 0.0;
          if (sscanf(cmdBuf + 9, "%d %f", &r, &ref) == 2) {
            uiController.showCalibrationWizardStart(r, ref);
            Serial.println("[WIZ] Started calibration wizard (see display)");
          } else Serial.println("[WIZ] Usage: WIZ_START <range_index 0..4> <ref_voltage>");
        } else if (strncmp(cmdBuf, "WIZ_SAVE", 8) == 0) {
          if (measurementEngine.saveCalibrationToEEPROM()) Serial.println("[WIZ] Saved wizard calibration to EEPROM"); else Serial.println("[WIZ] Save failed");
        } else if (strncmp(cmdBuf, "SET_POST", 8) == 0) {
          int n = 0; if (sscanf(cmdBuf + 8, "%d", &n) == 1) { dataLoggingManager.setPostAnomalySampleCount(n); dataLoggingManager.saveSettingsToEEPROM(); Serial.print("[SET] post-anom set to "); Serial.println(n); } else Serial.println("[SET] Usage: SET_POST <count>");
        } else if (strncmp(cmdBuf, "SET_SHOW", 8) == 0) {
          uiController.showSettingsMenu();
          Serial.print("[SET] Post-anom: "); Serial.println(dataLoggingManager.getPostAnomalySampleCount());
        } else if (strncmp(cmdBuf, "PROFILE_EXPORT", 14) == 0) {
          int idx=-1; if (sscanf(cmdBuf + 14, "%d", &idx) == 1) {
            char fname[32]; snprintf(fname, sizeof(fname), "profile_%d.csv", idx);
            if (measurementEngine.exportProfileToSD(idx, fname)) Serial.print("[PROFILE] Exported to "), Serial.println(fname); else Serial.println("[PROFILE] Export failed");
          } else Serial.println("[PROFILE] Usage: PROFILE_EXPORT <index>");
        } else if (strncmp(cmdBuf, "PROFILE_IMPORT", 14) == 0) {
          int idx=-1; if (sscanf(cmdBuf + 14, "%d", &idx) == 1) {
            char fname[32]; snprintf(fname, sizeof(fname), "profile_%d.csv", idx);
            if (measurementEngine.importProfileFromSD(idx, fname)) Serial.print("[PROFILE] Imported from "), Serial.println(fname); else Serial.println("[PROFILE] Import failed");
          } else Serial.println("[PROFILE] Usage: PROFILE_IMPORT <index>");
        } else if (strncmp(cmdBuf, "RUN_INTEGRATION", 15) == 0) {
          Serial.println("[TEST] Starting integration test...");
          runIntegrationTest();
        } else if (strncmp(cmdBuf, "SELFTEST", 8) == 0) {
          bool ok = true;
          Serial.println("[SELFTEST] Running self-test...");
          if (!measurementEngine.loadCalibrationFromEEPROM()) { Serial.println("[SELFTEST] Calibration load: FAIL"); ok = false; } else Serial.println("[SELFTEST] Calibration load: OK");
          if (!dataLoggingManager.isSDCardAvailable()) { Serial.println("[SELFTEST] SD card: NOT PRESENT"); ok = false; } else Serial.println("[SELFTEST] SD card: OK");
          // Basic osc check
          Serial.print("[SELFTEST] Osc buffer size: "); Serial.println(oscilloscopeEngine.getBufferSize());
          Serial.print("[SELFTEST] Valid samples available: "); Serial.println(oscilloscopeEngine.getValidSampleCount());
          Serial.print("[SELFTEST] Result: "); Serial.println(ok?"PASS":"FAIL");
        } else if (strncmp(cmdBuf, "AUTH_SETKEY", 11) == 0) {
          // Usage: AUTH_SETKEY <hexkey>
          const char* hex = cmdBuf + 11;
          while (*hex == ' ') ++hex;
          if (Comm::setHmacKeyFromHex(hex)) Serial.println("[AUTH] HMAC key set and persisted"); else Serial.println("[AUTH] Invalid hex key");
        } else if (strncmp(cmdBuf, "AUTH_MODE", 9) == 0) {
          // AUTH_MODE HMAC | PLAIN
          const char* arg = cmdBuf + 9;
          while (*arg == ' ') ++arg;
          if (strncmp(arg, "HMAC", 4) == 0) { Comm::enableHmac(true); Serial.println("[AUTH] Mode: HMAC"); }
          else { Comm::enableHmac(false); Serial.println("[AUTH] Mode: PLAIN"); }
        } else if (strncmp(cmdBuf, "OTA_SET_PUBKEY", 14) == 0) {
          // Usage: OTA_SET_PUBKEY <hex64bytes>
          const char* hex = cmdBuf + 14; while (*hex == ' ') ++hex;
          // hex must be 128 chars (64 bytes)
          int hlen = 0; const char* p = hex; while (*p) { ++p; ++hlen; }
          if (hlen != 128) { Serial.println("[OTA] Pubkey hex must be 128 chars (64 bytes)"); }
          else {
            uint8_t key[64]; bool bad=false;
            for (int i = 0; i < 64; ++i) {
              char hi = hex[i*2]; char lo = hex[i*2+1];
              auto val = [](char c)->int { if (c >= '0' && c <= '9') return c - '0'; if (c >= 'a' && c <= 'f') return c - 'a' + 10; if (c >= 'A' && c <= 'F') return c - 'A' + 10; return -1; };
              int vhi = val(hi); int vlo = val(lo);
              if (vhi < 0 || vlo < 0) { bad=true; break; }
              key[i] = (uint8_t)((vhi << 4) | vlo);
            }
            if (bad) Serial.println("[OTA] Invalid hex in pubkey");
            else {
              // persist: write magic then key
              EEPROM.write(EEPROM_OTA_PUBKEY_ADDR, 0xA5);
              for (int i = 0; i < 64; ++i) EEPROM.write(EEPROM_OTA_PUBKEY_ADDR + 1 + i, key[i]);
              Serial.println("[OTA] Public key saved to EEPROM");
            }
          }
        } else if (strncmp(cmdBuf, "OTA_CHECK", 9) == 0) {
          uint8_t pending = EEPROM.read(EEPROM_OTA_PUBKEY_ADDR + 128);
          Serial.print("[OTA] Pending update flag: "); Serial.println(pending);
        } else if (strncmp(cmdBuf, "OTA_APPLY", 9) == 0) {
          Serial.println("[OTA] Applying pending update (simulation)...");
          if (OTA::applyPendingUpdate()) Serial.println("[OTA] Apply simulation succeeded"); else Serial.println("[OTA] Apply simulation failed");
        } else if (strncmp(cmdBuf, "OTA_REBOOT_APPLY", 15) == 0) {
          Serial.println("[OTA] Requesting reboot to apply pending update...");
          OTA::requestRebootApply();
        } else if (strncmp(cmdBuf, "OTA_ROLLBACK", 12) == 0) {
          Serial.println("[OTA] Rolling back (simulation)");
          OTA::rollbackUpdate();
          Serial.println("[OTA] Rollback complete");
        } else if (strncmp(cmdBuf, "WDT_ON", 6) == 0) {
#ifdef __AVR__
          wdt_enable(WDTO_2S); wdtEnabled = true; Serial.println("[WDT] Watchdog enabled (2s)");
#else
          Serial.println("[WDT] Watchdog not supported on this platform");
#endif
        } else if (strncmp(cmdBuf, "WDT_OFF", 7) == 0) {
#ifdef __AVR__
          wdt_disable(); wdtEnabled = false; Serial.println("[WDT] Watchdog disabled");
#else
          Serial.println("[WDT] Watchdog not supported on this platform");
#endif
        } else {
          Serial.print("[CMD] Unknown: "); Serial.println(cmdBuf);
        }
        cmdIdx = 0; // reset buffer
      }
    } else {
      if (cmdIdx < (int)sizeof(cmdBuf) - 1) cmdBuf[cmdIdx++] = c;
    }
  }
}

