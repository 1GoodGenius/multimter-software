#include "measurement_engine.h"

MeasurementEngine::MeasurementEngine() {
  currentRange = RANGE_20V;
  autoRangingEnabled = true;

  // ADC settings for Arduino Mega (10-bit ADC, 5V reference)
  adcMaxValue = 1023;
  adcVref = 5.0f;

  // Smoothing defaults
  rawFiltered = 0.0f;
  smoothingAlpha = 0.25f; // moderate smoothing for autorange stability

  // Auto-range cooldown (ms)
  lastRangeChangeTime = 0;
  rangeChangeCooldownMs = 200;

  // Initialize calibration factors (default values, should be calibrated)
  calibrationFactors[RANGE_200MV] = 0.1;
  calibrationFactors[RANGE_2V] = 1.0;
  calibrationFactors[RANGE_20V] = 10.0;
  calibrationFactors[RANGE_200V] = 100.0;
  calibrationFactors[RANGE_1000V] = 500.0;

  // Initialize current calibration
  currentCalibrationFactor = 1.0;
  currentOffset = adcVref / 2.0f; // assume mid-rail by default
  overloadCallback = nullptr;
  wasOverloaded = false;

  // Initialize overload thresholds (in volts)
  overloadThresholds[RANGE_200MV] = 0.25;
  overloadThresholds[RANGE_2V] = 2.5;
  overloadThresholds[RANGE_20V] = 25.0;
  overloadThresholds[RANGE_200V] = 250.0;
  overloadThresholds[RANGE_1000V] = 1200.0;
} 

bool MeasurementEngine::initialize() {
  // For Arduino Mega we use the built-in analogRead (10-bit, 0..1023)

  // Initialize range selection pins
  pinMode(RANGE_PIN_200MV, OUTPUT);
  pinMode(RANGE_PIN_2V, OUTPUT);
  pinMode(RANGE_PIN_20V, OUTPUT);
  pinMode(RANGE_PIN_200V, OUTPUT);
  pinMode(RANGE_PIN_1000V, OUTPUT);

  // Set a default range on startup
  setRange(currentRange);

  return true;
} 

float MeasurementEngine::readRawVoltage() {
  // Return ADC input voltage (before divider) in volts, no calibration, no auto-ranging
  int rawValue = analogRead(VOLTAGE_ADC_PIN);
  float voltage = (rawValue / (float)adcMaxValue) * adcVref;
  // Update EWMA filtered value for autorange stability
  if (rawFiltered <= 0.0f) rawFiltered = voltage; // seed
  rawFiltered = smoothingAlpha * voltage + (1.0f - smoothingAlpha) * rawFiltered;
  return rawFiltered; // use filtered reading to avoid chattering
}

float MeasurementEngine::readVoltage() {
  float raw = readRawVoltage();
  float voltage = raw * calibrationFactors[currentRange]; // Apply calibration for current range

  // Auto-ranging if enabled (non-recursive - performAutoRanging uses raw reads)
  if (autoRangingEnabled) {
    bool changed = performAutoRanging();
    if (changed) {
      // Recompute with new range
      raw = readRawVoltage();
      voltage = raw * calibrationFactors[currentRange];
    }
  }

  return voltage;
} 

float MeasurementEngine::readCurrent() {
  int rawValue = analogRead(CURRENT_ADC_PIN);
  float v = (rawValue / (float)adcMaxValue) * adcVref;

  // Apply offset and sensitivity to convert voltage to current
  float corrected = (v - currentOffset) * currentCalibrationFactor; // user-cal registrable

  // Example: if sensor is 0.1 V/A then current = corrected / 0.1
  // Here we assume a 0.1 V/A default sensitivity; you should tune this per hardware
  float current = corrected / 0.1f;

  return current;
} 

bool MeasurementEngine::setRange(VoltageRange range) {
  if (range < 0 || range > 4) return false;
  
  currentRange = range;
  
  // Deactivate all range selection pins first
  digitalWrite(RANGE_PIN_200MV, LOW);
  digitalWrite(RANGE_PIN_2V, LOW);
  digitalWrite(RANGE_PIN_20V, LOW);
  digitalWrite(RANGE_PIN_200V, LOW);
  digitalWrite(RANGE_PIN_1000V, LOW);
  
  // Activate the selected range's pin
  switch (range) {
    case RANGE_200MV:
      digitalWrite(RANGE_PIN_200MV, HIGH);
      break;
    case RANGE_2V:
      digitalWrite(RANGE_PIN_2V, HIGH);
      break;
    case RANGE_20V:
      digitalWrite(RANGE_PIN_20V, HIGH);
      break;
    case RANGE_200V:
      digitalWrite(RANGE_PIN_200V, HIGH);
      break;
    case RANGE_1000V:
      digitalWrite(RANGE_PIN_1000V, HIGH);
      break;
  }
  
  return true;
}

VoltageRange MeasurementEngine::getCurrentRange() {
  return currentRange;
}

void MeasurementEngine::enableAutoRanging(bool enable) {
  autoRangingEnabled = enable;
}

bool MeasurementEngine::performAutoRanging() {
  // Use raw reads and calibration factor for decision-making to avoid recursion
  float raw = readRawVoltage();
  float measured = raw * calibrationFactors[currentRange];
  VoltageRange newRange = currentRange;

  unsigned long now = millis();
  if (now - lastRangeChangeTime < rangeChangeCooldownMs) {
    // Cooldown not elapsed
    return false;
  }

  // Hysteresis thresholds to avoid chattering
  float highThreshold = overloadThresholds[currentRange] * 0.9f;
  float lowThreshold = overloadThresholds[currentRange] * 0.2f;

  if (measured > highThreshold) {
    // Need higher range
    if (currentRange < RANGE_1000V) {
      newRange = static_cast<VoltageRange>(currentRange + 1);
    }
  } else if (measured < lowThreshold) {
    // Can use lower range
    if (currentRange > RANGE_200MV) {
      newRange = static_cast<VoltageRange>(currentRange - 1);
    }
  }

  if (newRange != currentRange) {
    setRange(newRange);
    lastRangeChangeTime = now;
    return true;
  }

  return false;
} 

bool MeasurementEngine::isOverloaded() {
  float raw = readRawVoltage();
  float measured = raw * calibrationFactors[currentRange];
  return measured > overloadThresholds[currentRange];
}

float MeasurementEngine::getCalibrationFactor(VoltageRange range) {
  if (range < 0 || range > 4) return 1.0;
  return calibrationFactors[range];
}

void MeasurementEngine::setCalibrationFactor(VoltageRange range, float factor) {
  if (range >= 0 && range <= 4) {
    calibrationFactors[range] = factor;
  }
}

Measurement MeasurementEngine::getMeasurement() {
  Measurement m;
  m.voltage = readVoltage();
  m.current = readCurrent();
  m.timestamp = millis();
  return m;
}

void MeasurementEngine::update() {
  // Check overload state and call callback if changed
  bool overloaded = isOverloaded();
  if (overloaded != wasOverloaded) {
    wasOverloaded = overloaded;
    if (overloadCallback) overloadCallback(overloaded);
  }
}

void MeasurementEngine::setOverloadCallback(OverloadCallback cb) {
  overloadCallback = cb;
}

void MeasurementEngine::setSmoothingAlpha(float a) {
  if (a <= 0.0f) a = 0.01f;
  if (a > 1.0f) a = 1.0f;
  smoothingAlpha = a;
}

float MeasurementEngine::getSmoothingAlpha() {
  return smoothingAlpha;
}

// ------------------- EEPROM-backed calibration -------------------
#include <EEPROM.h>

struct PersistedCalibration {
  uint16_t magic;
  uint8_t version;
  float calibrationFactors[5];
  float currentCalibrationFactor;
  float currentOffset;
  uint16_t postAnomalySampleCount;
  uint8_t reserved[10];
};

bool MeasurementEngine::loadCalibrationFromEEPROM() {
  PersistedCalibration p;
  EEPROM.get(EEPROM_CALIB_ADDR, p);
  if (p.magic != EEPROM_CALIB_MAGIC || p.version != EEPROM_CALIB_VERSION) {
    // No valid calibration stored
    return false;
  }
  for (int i = 0; i < 5; i++) calibrationFactors[i] = p.calibrationFactors[i];
  currentCalibrationFactor = p.currentCalibrationFactor;
  currentOffset = p.currentOffset;
  // also restore post-anomaly sample count if desired
  // postAnomalySampleCount = p.postAnomalySampleCount;
  return true;
}

bool MeasurementEngine::saveCalibrationToEEPROM() {
  PersistedCalibration p;
  p.magic = EEPROM_CALIB_MAGIC;
  p.version = EEPROM_CALIB_VERSION;
  for (int i = 0; i < 5; i++) p.calibrationFactors[i] = calibrationFactors[i];
  p.currentCalibrationFactor = currentCalibrationFactor;
  p.currentOffset = currentOffset;
  EEPROM.put(EEPROM_CALIB_ADDR, p);
  return true;
}

void MeasurementEngine::resetCalibration() {
  calibrationFactors[RANGE_200MV] = 0.1f;
  calibrationFactors[RANGE_2V] = 1.0f;
  calibrationFactors[RANGE_20V] = 10.0f;
  calibrationFactors[RANGE_200V] = 100.0f;
  calibrationFactors[RANGE_1000V] = 500.0f;

  currentCalibrationFactor = 1.0f;
  currentOffset = adcVref / 2.0f;
}

float MeasurementEngine::calibrateRange(VoltageRange range, float referenceVoltage, int samples) {
  // Read multiple raw samples (no auto-ranging) and compute calibration factor
  unsigned long sumRaw = 0;
  for (int i = 0; i < samples; i++) {
    int raw = analogRead(VOLTAGE_ADC_PIN);
    sumRaw += raw;
    delay(5);
  }
  float avgRaw = (float)sumRaw / (float)samples;
  float measuredVoltage = (avgRaw / (float)adcMaxValue) * adcVref;
  if (measuredVoltage <= 0.0f) return NAN;
  float factor = referenceVoltage / measuredVoltage;
  calibrationFactors[range] = factor;
  return factor;
}

float MeasurementEngine::calibrateCurrentZero(int samples) {
  unsigned long sumRaw = 0;
  for (int i = 0; i < samples; i++) {
    int raw = analogRead(CURRENT_ADC_PIN);
    sumRaw += raw;
    delay(5);
  }
  float avgRaw = (float)sumRaw / (float)samples;
  float v = (avgRaw / (float)adcMaxValue) * adcVref;
  currentOffset = v;
  return currentOffset;
}

float MeasurementEngine::calibrateCurrentKnown(float knownCurrentAmps, int samples) {
  // Assumes zero has been calibrated via calibrateCurrentZero
  unsigned long sumRaw = 0;
  for (int i = 0; i < samples; i++) {
    int raw = analogRead(CURRENT_ADC_PIN);
    sumRaw += raw;
    delay(5);
  }
  float avgRaw = (float)sumRaw / (float)samples;
  float v = (avgRaw / (float)adcMaxValue) * adcVref;
  float delta = v - currentOffset;
  if (fabs(knownCurrentAmps) < 1e-6f) return NAN;
  currentCalibrationFactor = delta / knownCurrentAmps; // volts per amp
  return currentCalibrationFactor;
}

void MeasurementEngine::printCalibration(Print &out) {
  out.println("Calibration:");
  for (int i = 0; i < 5; i++) {
    out.print(" Range "); out.print(i); out.print(": factor="); out.println(calibrationFactors[i], 6);
  }
  out.print("Current offset (V): "); out.println(currentOffset, 6);
  out.print("Current calibration (V/A): "); out.println(currentCalibrationFactor, 6);
}

// Non-blocking calibration state
static bool _calibrating = false;
static VoltageRange _cal_range = RANGE_20V;
static float _cal_ref = 0.0f;
static int _cal_samples_total = 0;
static int _cal_samples_done = 0;
static float _cal_accum = 0.0f;
static float _cal_result = NAN;

bool MeasurementEngine::startRangeCalibration(VoltageRange range, float referenceVoltage, int samples) {
  if (referenceVoltage <= 0.0f || samples <= 0) return false;
  _calibrating = true;
  _cal_range = range;
  _cal_ref = referenceVoltage;
  _cal_samples_total = samples;
  _cal_samples_done = 0;
  _cal_accum = 0.0f;
  _cal_result = NAN;
  setRange(range);
  return true;
}

bool MeasurementEngine::performCalibrationStep() {
  if (!_calibrating) return false;
  int raw = analogRead(VOLTAGE_ADC_PIN);
  _cal_accum += (raw / (float)adcMaxValue) * adcVref;
  _cal_samples_done++;
  if (_cal_samples_done >= _cal_samples_total) {
    float avg = _cal_accum / (float)_cal_samples_total;
    if (avg <= 1e-9f) {
      _cal_result = NAN;
    } else {
      _cal_result = _cal_ref / avg;
      calibrationFactors[_cal_range] = _cal_result;
    }
    _calibrating = false;
    return true;
  }
  return false;
}

float MeasurementEngine::getLastRangeCalibrationResult() {
  return _cal_result;
}
void MeasurementEngine::cancelRangeCalibration() {
  _calibrating = false;
  _cal_result = NAN;
}

bool MeasurementEngine::isRangeCalibrationActive() {
  return _calibrating;
}

int MeasurementEngine::getCalibrationProgress() {
  if (!_calibrating || _cal_samples_total <= 0) return 0;
  return (int)((_cal_samples_done * 100) / _cal_samples_total);
}

// ------------------- Profile persistence -------------------
struct PersistedProfile {
  uint16_t magic;
  char name[PROFILE_NAME_LEN];
  float calibrationFactors[5];
  float currentCalibrationFactor;
  float currentOffset;
  uint8_t reserved[4];
};

static inline int profileAddress(int index) {
  return EEPROM_PROFILES_ADDR + index * sizeof(PersistedProfile);
}

bool MeasurementEngine::saveProfile(int index, const char* name) {
  if (index < 0 || index >= MAX_CAL_PROFILES) return false;
  PersistedProfile p;
  p.magic = EEPROM_PROFILE_MAGIC;
  memset(p.name, 0, sizeof(p.name));
  strncpy(p.name, name, sizeof(p.name)-1);
  for (int i=0;i<5;i++) p.calibrationFactors[i] = calibrationFactors[i];
  p.currentCalibrationFactor = currentCalibrationFactor;
  p.currentOffset = currentOffset;
  EEPROM.put(profileAddress(index), p);
  return true;
}

bool MeasurementEngine::loadProfile(int index) {
  if (index < 0 || index >= MAX_CAL_PROFILES) return false;
  PersistedProfile p;
  EEPROM.get(profileAddress(index), p);
  if (p.magic != EEPROM_PROFILE_MAGIC) return false;
  for (int i=0;i<5;i++) calibrationFactors[i] = p.calibrationFactors[i];
  currentCalibrationFactor = p.currentCalibrationFactor;
  currentOffset = p.currentOffset;
  return true;
}

bool MeasurementEngine::deleteProfile(int index) {
  if (index < 0 || index >= MAX_CAL_PROFILES) return false;
  PersistedProfile p;
  memset(&p,0,sizeof(p));
  EEPROM.put(profileAddress(index), p);
  return true;
}

void MeasurementEngine::listProfiles(Print &out) {
  for (int i=0;i<MAX_CAL_PROFILES;i++) {
    PersistedProfile p;
    EEPROM.get(profileAddress(i), p);
    out.print("Profile "); out.print(i); out.print(": ");
    if (p.magic == EEPROM_PROFILE_MAGIC) out.println(p.name);
    else out.println("<empty>");
  }
}

#include <SD.h>

bool MeasurementEngine::getProfileName(int index, char* outBuf, int bufLen) {
  if (index < 0 || index >= MAX_CAL_PROFILES) return false;
  PersistedProfile p;
  EEPROM.get(profileAddress(index), p);
  if (p.magic != EEPROM_PROFILE_MAGIC) return false;
  strncpy(outBuf, p.name, bufLen-1);
  outBuf[bufLen-1] = '\0';
  return true;
}

bool MeasurementEngine::exportProfileToSD(int index, const char* filename) {
  if (index < 0 || index >= MAX_CAL_PROFILES) return false;
  PersistedProfile p;
  EEPROM.get(profileAddress(index), p);
  if (p.magic != EEPROM_PROFILE_MAGIC) return false;
  if (!SD.begin()) return false;
  File f = SD.open(filename, FILE_WRITE);
  if (!f) return false;
  // CSV: name,f0,f1,f2,f3,f4,currCal,currOffset
  f.print(p.name);
  for (int i=0;i<5;i++) {
    f.print(','); f.print(p.calibrationFactors[i], 6);
  }
  f.print(','); f.print(p.currentCalibrationFactor, 6);
  f.print(','); f.print(p.currentOffset, 6);
  f.println();
  f.close();
  return true;
}

bool MeasurementEngine::importProfileFromSD(int index, const char* filename) {
  if (index < 0 || index >= MAX_CAL_PROFILES) return false;
  if (!SD.begin()) return false;
  if (!SD.exists(filename)) return false;
  File f = SD.open(filename, FILE_READ);
  if (!f) return false;
  // Read the entire first line
  char buf[256];
  int read = f.readBytesUntil('\n', buf, sizeof(buf)-1);
  buf[read] = '\0';
  f.close();

  // Parse CSV
  // Expected: name,f0,f1,f2,f3,f4,currCal,currOffset
  char* tok = strtok(buf, ",");
  if (!tok) return false;
  PersistedProfile p;
  memset(&p,0,sizeof(p));
  p.magic = EEPROM_PROFILE_MAGIC;
  strncpy(p.name, tok, sizeof(p.name)-1);
  for (int i=0;i<5;i++) {
    tok = strtok(NULL, ","); if (!tok) return false;
    p.calibrationFactors[i] = atof(tok);
  }
  tok = strtok(NULL, ","); if (!tok) return false; p.currentCalibrationFactor = atof(tok);
  tok = strtok(NULL, ","); if (!tok) return false; p.currentOffset = atof(tok);
  EEPROM.put(profileAddress(index), p);
  return true;
}
