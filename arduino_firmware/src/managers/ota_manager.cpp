#include "ota_manager.h"
#include <EEPROM.h>
#include <SD.h>
#include <Arduino.h>

// EEPROM layout (reuse existing offsets)
#define EEPROM_OTA_PUBKEY_ADDR 0x500
#define EEPROM_OTA_PENDING_FLAG (EEPROM_OTA_PUBKEY_ADDR + 128)
#define PENDING_FILE "pending_update.bin"
#define APPLIED_FILE "applied_update.bin"

namespace OTA {

void begin() {
  // No-op for now; placeholder for initial checks
}

bool hasPendingUpdate() {
  uint8_t pending = EEPROM.read(EEPROM_OTA_PENDING_FLAG);
  return pending == 1;
}

bool applyPendingUpdate() {
  // In production this would call bootloader and write flash. For now we'll simulate by
  // moving pending_update.bin -> applied_update.bin on SD and clearing the pending flag.
  if (!SD.begin()) return false;
  if (!SD.exists(PENDING_FILE)) return false;
  // remove old applied file
  if (SD.exists(APPLIED_FILE)) SD.remove(APPLIED_FILE);
  // rename by copying
  File src = SD.open(PENDING_FILE, FILE_READ);
  if (!src) return false;
  File dst = SD.open(APPLIED_FILE, FILE_WRITE);
  if (!dst) { src.close(); return false; }
  const size_t BUF = 256;
  uint8_t buf[BUF];
  while (src.available()) {
    size_t r = src.read(buf, BUF);
    dst.write(buf, r);
  }
  dst.flush(); dst.close(); src.close();
  // Clear pending flag
  EEPROM.write(EEPROM_OTA_PENDING_FLAG, 0);
  return true;
}

void requestRebootApply() {
  // Set pending flag and reboot via watchdog to hand-off to bootloader
  EEPROM.write(EEPROM_OTA_PENDING_FLAG, 1);
#ifdef __AVR__
  // small delay to ensure EEPROM write completes
  delay(50);
  // enable watchdog for immediate reset
  wdt_enable(WDTO_15MS);
  while (1) { } // wait for watchdog
#else
  // For non-AVR platforms, perform software reset
  NVIC_SystemReset();
#endif
}

void rollbackUpdate() {
  // For simulation, delete applied update and set pending flag to 0
  if (SD.begin()) {
    if (SD.exists(APPLIED_FILE)) SD.remove(APPLIED_FILE);
  }
  EEPROM.write(EEPROM_OTA_PENDING_FLAG, 0);
}

}
