#ifndef OTA_MANAGER_H
#define OTA_MANAGER_H

#include <stdint.h>

// EEPROM layout (reuse existing offsets)
#define EEPROM_OTA_PUBKEY_ADDR 0x500
#define EEPROM_OTA_PENDING_FLAG (EEPROM_OTA_PUBKEY_ADDR + 128)

namespace OTA {

// Check if a pending validated update exists
bool hasPendingUpdate();
// Apply pending update (calls bootloader/apply mechanism). Returns true if applied OK.
bool applyPendingUpdate();
// Request the bootloader to apply a pending update: sets pending flag and forces reset.
void requestRebootApply();
// Trigger simulated rollback (for testing)
void rollbackUpdate();

// Initialize OTA subsystem (call from setup)
void begin();

}

#endif // OTA_MANAGER_H
