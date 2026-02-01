#ifndef MEASUREMENT_ENGINE_H
#define MEASUREMENT_ENGINE_H

#include <Arduino.h>
#include "ADC.h"
#include "smart_oscilloscope.h"

class MeasurementEngine {
private:
  VoltageRange currentRange;
  float calibrationFactors[5]; // Calibration factors for each range
  float overloadThresholds[5]; // Voltage thresholds for overload detection
  bool autoRangingEnabled;

  // Auto-ranging cooldown and hysteresis
  unsigned long lastRangeChangeTime;
  unsigned long rangeChangeCooldownMs;

  // ADC characteristics for Arduino Mega (10-bit, 5V ref)
  int adcMaxValue;
  float adcVref;

  // Simple smoothing for raw ADC values to reduce noise in autoranging
  float rawFiltered;
  float smoothingAlpha; // 0..1 (EWMA), higher = more responsive
  void setSmoothingAlpha(float a);
  float getSmoothingAlpha();

  // Overload callback
  typedef void (*OverloadCallback)(bool overloaded);
  void setOverloadCallback(OverloadCallback cb);
  OverloadCallback overloadCallback;
  bool wasOverloaded;
  // Current channel calibration
  float currentCalibrationFactor;
  float currentOffset; // voltage offset at sensor (e.g., mid-rail)

  // Low-level read helper that does not trigger auto-ranging
  float readRawVoltage();

public:
  MeasurementEngine();
  bool initialize();
  float readVoltage();
  float readCurrent();
  bool setRange(VoltageRange range);
  VoltageRange getCurrentRange();
  void enableAutoRanging(bool enable);
  bool performAutoRanging();
  bool isOverloaded();
  float getCalibrationFactor(VoltageRange range);
  void setCalibrationFactor(VoltageRange range, float factor);
  Measurement getMeasurement();
  void update();

  // Calibration & EEPROM
  bool loadCalibrationFromEEPROM();
  bool saveCalibrationToEEPROM();
  void resetCalibration();

  // Calibration routines
  float calibrateRange(VoltageRange range, float referenceVoltage, int samples = 50);
  // Non-blocking calibration API (step-driven)
  bool startRangeCalibration(VoltageRange range, float referenceVoltage, int samples = 50);
  bool performCalibrationStep(); // returns true if step completed and calibration finished
  void cancelRangeCalibration();
  bool isRangeCalibrationActive();
  int getCalibrationProgress(); // 0..100
  float getLastRangeCalibrationResult();

  float calibrateCurrentZero(int samples = 50);
  float calibrateCurrentKnown(float knownCurrentAmps, int samples = 50);
  void printCalibration(Print &out = Serial);

  // Profile management
  bool saveProfile(int index, const char* name);
  bool loadProfile(int index);
  bool deleteProfile(int index);
  void listProfiles(Print &out = Serial);
  bool getProfileName(int index, char* outBuf, int bufLen);

  // Export/import profiles to/from SD (CSV format for interoperability)
  bool exportProfileToSD(int index, const char* filename);
  bool importProfileFromSD(int index, const char* filename);
};

#endif // MEASUREMENT_ENGINE_H