#include <iostream>
#include <cmath>

// Simulate the calibration math used by MeasurementEngine::calibrateRange
float computeFactorFromRawAvg(float avgRaw, float adcMaxValue, float adcVref, float referenceVoltage) {
  float measuredVoltage = (avgRaw / adcMaxValue) * adcVref;
  if (measuredVoltage <= 0.0f) return NAN;
  return referenceVoltage / measuredVoltage;
}

int main() {
  float avgRaw = 512.0f; // mid-scale on 10-bit ADC
  float adcMax = 1023.0f;
  float vref = 5.0f;
  float refVoltage = 2.0f; // suppose we connected 2.0V reference

  float factor = computeFactorFromRawAvg(avgRaw, adcMax, vref, refVoltage);
  std::cout << "Computed factor: " << factor << "\n";
  float expected = refVoltage / ((avgRaw / adcMax) * vref);
  if (fabs(factor - expected) < 1e-6f) {
    std::cout << "Calibration math test passed.\n";
    return 0;
  } else {
    std::cout << "Calibration math test failed. expected=" << expected << "\n";
    return 1;
  }
}
