/*
 * Digital Multimeter Header File
 * Contains all function declarations, constants, and data structures
 */

#ifndef MULTIMETER_H
#define MULTIMETER_H

#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <EEPROM.h>

// Version Information
#define FIRMWARE_VERSION "1.0.0"
#define HARDWARE_VERSION "1.0"

// Hardware Configuration
#define LCD_ADDRESS 0x27
#define LCD_COLS 20
#define LCD_ROWS 4
#define I2C_SDA_PIN A4
#define I2C_SCL_PIN A5

// Pin Definitions
#define VOLTAGE_INPUT A0
#define CURRENT_INPUT A1
#define VOLTAGE_SELECT_PIN 2
#define CURRENT_SELECT_PIN 3
#define RELAY_CONTROL_PIN 4
#define BUZZER_PIN 5
#define BACKLIGHT_PIN 6
#define ROTARY_A 7
#define ROTARY_B 8
#define ROTARY_BUTTON 9
#define MODE_BUTTON 10
#define HOLD_BUTTON 11
#define RANGE_BUTTON 12
#define TEMP_SENSOR A2
#define BATTERY_MONITOR A3

// Timing Constants
#define UPDATE_INTERVAL 200      // Display update interval (ms)
#define DEBOUNCE_DELAY 50        // Button debounce delay (ms)
#define CONTINUITY_BEEP_INTERVAL 500  // Continuity beep interval (ms)
#define STARTUP_DELAY 2000       // Startup screen duration (ms)
#define SAMPLE_DELAY_US 100      // Delay between samples (microseconds)

// Measurement Constants
#define ADC_RESOLUTION 1023.0
#define REFERENCE_VOLTAGE 5.0
#define VOLTAGE_DIVIDER_RATIO 50.0
#define SHUNT_RESISTANCE 0.1     // Ohms
#define CONTINUITY_THRESHOLD 50.0  // Ohms
#define DIODE_TEST_CURRENT 0.001 // 1mA test current

// Frequency Measurement
#define FREQUENCY_MEASUREMENT_WINDOW 100000  // microseconds
#define MIN_PULSE_WIDTH 10        // microseconds

// Temperature Constants (LM35)
#define TEMP_COEFFICIENT 100.0    // 10mV/°C for LM35
#define TEMP_OFFSET_CELSIUS 0.0

// Battery Monitoring
#define BATTERY_VOLTAGE_DIVIDER 2.0
#define LOW_BATTERY_THRESHOLD 3.3 // Volts
#define CRITICAL_BATTERY_THRESHOLD 3.0 // Volts

// EEPROM Addresses
#define CALIBRATION_ADDRESS 0
#define SETTINGS_ADDRESS sizeof(CalibrationData)

// Calibration Data Structure
struct CalibrationData {
  float voltage_offset;
  float voltage_scale;
  float current_offset;
  float current_scale;
  float resistance_offset;
  float resistance_scale;
  float temp_offset;
  float temp_scale;
  // Add checksum for data integrity
  uint16_t checksum;
};

// Settings Structure
struct Settings {
  bool auto_range;
  bool beep_enabled;
  bool backlight_auto_off;
  unsigned long backlight_timeout;
  bool data_logging;
  unsigned long log_interval;
  uint8_t contrast;
  uint8_t brightness;
  uint16_t checksum;
};

// Measurement Modes Enumeration
enum MeasurementMode {
  MODE_DC_VOLTAGE = 0,
  MODE_AC_VOLTAGE,
  MODE_DC_CURRENT,
  MODE_AC_CURRENT,
  MODE_RESISTANCE,
  MODE_CONTINUITY,
  MODE_DIODE,
  MODE_FREQUENCY,
  MODE_TEMPERATURE,
  MODE_COUNT
};

// Range Setting Structure
struct RangeSetting {
  float max_value;
  float resolution;
  int decimal_places;
  const char* unit;
  const char* prefix;
};

// Error Codes
enum ErrorCode {
  ERROR_NONE = 0,
  ERROR_OVER_RANGE,
  ERROR_UNDER_RANGE,
  ERROR_OPEN_CIRCUIT,
  ERROR_SHORT_CIRCUIT,
  ERROR_SENSOR_FAULT,
  ERROR_CALIBRATION_INVALID,
  ERROR_MEMORY_FULL,
  ERROR_COMMUNICATION_FAILED
};

// Measurement Result Structure
struct MeasurementResult {
  float value;
  ErrorCode error;
  uint32_t timestamp;
  float noise_level;
  bool stable;
};

// Function Declarations

// Initialization and Setup
void initializeHardware();
void loadCalibration();
void saveCalibration();
void loadSettings();
void saveSettings();
void displayStartupScreen();
void validateCalibration();

// Measurement Functions
void performMeasurement();
MeasurementResult measureDCVoltage();
MeasurementResult measureACVoltage();
MeasurementResult measureDCCurrent();
MeasurementResult measureACCurrent();
MeasurementResult measureResistance();
MeasurementResult measureContinuity();
MeasurementResult measureDiode();
MeasurementResult measureFrequency();
MeasurementResult measureTemperature();

// Enhanced Measurement with Filtering
float getFilteredReading(int pin, int samples = 10);
float getAverageReading(int pin, int samples = 50);
float getRMSReading(int pin, int samples = 100);
bool isStableReading(float* readings, int count, float threshold = 0.01);

// Range Management
void autoRange();
void setManualRange(int range_index);
bool isValidRange(MeasurementMode mode, int range_index);
RangeSetting* getCurrentRange();
RangeSetting* getRange(MeasurementMode mode, int index);
int getRangeCount(MeasurementMode mode);

// Display Functions
void updateDisplay();
void displayFormattedValue(float value, RangeSetting* range);
void displayError(ErrorCode error);
void displayStatus();
void displayBatteryStatus();
void displayRangeInfo();
void clearDisplayLine(int line);

// Input Handling
void handleButtons();
void handleRotaryEncoder();
void debounceInputs();
bool isButtonPressed(int pin);
void handleLongPress(int pin);

// Mode Management
void setMeasurementMode(MeasurementMode mode);
void cycleMode(int direction = 1);
const char* getModeName(MeasurementMode mode);
const char* getModeUnit(MeasurementMode mode);

// Continuity and Audio
void handleContinuityBeep();
void beep(int frequency = 2000, int duration = 100);
void beepError();
void beepSuccess();

// Battery Management
float readBatteryVoltage();
bool isLowBattery();
bool isCriticalBattery();
void handleLowBattery();

// Data Logging
void logData();
void startLogging();
void stopLogging();
void flushLogBuffer();
bool isLoggingEnabled();

// Serial Communication
void handleSerialCommands();
void processCalibrationCommand(String command);
void processGetCommand(String command);
void processSetCommand(String command);
void sendStatus();
void sendReading();

// Calibration Functions
void enterCalibrationMode();
void calibrateVoltage();
void calibrateCurrent();
void calibrateResistance();
void calibrateTemperature();
void resetCalibration();
bool verifyCalibration();

// Utility Functions
float mapFloat(float x, float in_min, float in_max, float out_min, float out_max);
bool approximatelyEqual(float a, float b, float epsilon = 0.0001);
float calculateNoiseLevel(float* readings, int count);
uint16_t calculateChecksum(const void* data, size_t length);
void delayMicrosecondsAccurate(unsigned long us);

// Advanced Features
void performSelfTest();
bool runDiagnostics();
void displayDiagnosticResults();
void factoryReset();

// Menu System (if implemented)
void enterMenuMode();
void handleMenuNavigation();
void displayMenu();
void executeMenuItem(int item);

// External Communication (if implemented)
bool sendDataViaBluetooth();
bool sendDataViaWiFi();
void handleRemoteCommands();

// Constants for Range Arrays
extern RangeSetting dc_voltage_ranges[];
extern RangeSetting ac_voltage_ranges[];
extern RangeSetting dc_current_ranges[];
extern RangeSetting ac_current_ranges[];
extern RangeSetting resistance_ranges[];
extern const char* mode_names[];

// Global Variables (extern declarations)
extern LiquidCrystal_I2C lcd;
extern CalibrationData cal;
extern Settings settings;
extern MeasurementMode current_mode;
extern int current_range_index;
extern bool hold_enabled;
extern bool backlight_on;
extern float last_reading;
extern unsigned long last_update_time;
extern MeasurementResult last_result;

// Interrupt Service Routine Declarations (if needed)
void rotaryEncoderISR();
void buttonISR();

// Debug Functions
#ifdef DEBUG
void debugPrint(String message);
void debugPrintValue(String name, float value);
void printMemoryUsage();
void printTimingInfo();
#endif

// Compile-time Configuration
#ifndef SAMPLES_PER_READING
#define SAMPLES_PER_READING 10
#endif

#ifndef FILTER_ENABLED
#define FILTER_ENABLED true
#endif

#ifndef AUTO_RANGE_ENABLED
#define AUTO_RANGE_ENABLED true
#endif

#ifndef BATTERY_MONITORING_ENABLED
#define BATTERY_MONITORING_ENABLED true
#endif

#ifndef DATA_LOGGING_ENABLED
#define DATA_LOGGING_ENABLED false
#endif

// Hardware Version Specific Defines
#ifdef HARDWARE_VERSION_2_0
  // Version 2.0 specific pin assignments
  #define VOLTAGE_INPUT A0
  #define CURRENT_INPUT A1
#elif defined(HARDWARE_VERSION_1_0)
  // Version 1.0 specific pin assignments
  #define VOLTAGE_INPUT A0
  #define CURRENT_INPUT A1
#endif

#endif // MULTIMETER_H