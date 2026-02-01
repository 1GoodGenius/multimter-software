#ifndef SMART_OSCILLOSCOPE_H
#define SMART_OSCILLOSCOPE_H

#include <Arduino.h>
#include "ADC.h"
#include <ILI9341_t3.h>
#include <XPT2046_Touchscreen.h>
#include <Encoder.h>
#include <SD.h>
#include <SPI.h>
#include <Wire.h>

// Pin Definitions
#define VOLTAGE_ADC_PIN A0
#define CURRENT_ADC_PIN A1
#define TFT_CS_PIN 10
#define TFT_DC_PIN 9
#define TOUCH_CS_PIN 8
#define TOUCH_IRQ_PIN 7
#define ENCODER_A_PIN 2
#define ENCODER_B_PIN 3
#define ENCODER_BTN_PIN 4
#define SD_CS_PIN 6

// Range Selection Pins (for MOSFET-based voltage dividers)
#define RANGE_PIN_200MV   14
#define RANGE_PIN_2V      15
#define RANGE_PIN_20V     16
#define RANGE_PIN_200V    17
#define RANGE_PIN_1000V   18

// Measurement Ranges
enum VoltageRange {
  RANGE_200MV,
  RANGE_2V,
  RANGE_20V,
  RANGE_200V,
  RANGE_1000V
};

enum TriggerEdge {
  TRIGGER_RISING,
  TRIGGER_FALLING,
  TRIGGER_BOTH
};

// Data Structures
struct Measurement {
  float voltage;
  float current;
  unsigned long timestamp;
};

struct WaveformSample {
  float value;
  unsigned long timestamp;
};

struct LogEntry {
  Measurement measurement;
  bool anomaly;
  unsigned long timestamp;
};

// Packet Protocol
struct Packet {
  uint8_t header[4] = {'S', 'O', 'S', 'C'};
  uint8_t command;
  uint16_t payloadLength;
  uint8_t* payload;
  uint8_t checksum;
};

// Commands
#define CMD_SET_RANGE 0x01
#define CMD_START_CAPTURE 0x02
#define CMD_STOP_CAPTURE 0x03
#define CMD_SET_TRIGGER 0x04
#define CMD_CALC_INPUT 0x05
#define CMD_GET_LOGS 0x06
#define CMD_MEASUREMENT_DATA 0x10
#define CMD_WAVEFORM_DATA 0x11
#define CMD_CALC_RESULT 0x12
#define CMD_LOG_DATA 0x13
#define CMD_SAFETY_ALERT 0x14

// Default buffer sizes tuned for ATmega2560 (8KB SRAM)
#define DEFAULT_OSC_BUFFER_SIZE 512
#define DEFAULT_LOG_CIRCULAR_SIZE 128
#define DEFAULT_LOG_ANOMALY_SIZE 64
#define MAX_SAFE_LOG_ENTRIES 256 // Warn if user requests more than this

// Low-memory (UNO - ATmega328P) overrides
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

// EEPROM calibration storage
#define EEPROM_CALIB_MAGIC 0xCA11
#define EEPROM_CALIB_ADDR 0
#define EEPROM_CALIB_VERSION 1
#define EEPROM_CALIB_SIZE_BYTES 64 // reserved size for calibration struct (must be sufficient) 

// Profile storage
#define MAX_CAL_PROFILES 4
#define PROFILE_NAME_LEN 12
#define EEPROM_PROFILES_ADDR (EEPROM_CALIB_ADDR + EEPROM_CALIB_SIZE_BYTES + 128)
#define EEPROM_PROFILE_MAGIC 0xC0DE
#define EEPROM_PROFILE_SIZE_BYTES 48 // per-profile reserved bytes



#endif // SMART_OSCILLOSCOPE_H