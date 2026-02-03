#include "data_logging_manager.h"

// --- Constructor / Destructor ---

DataLoggingManager::DataLoggingManager(int circularSize, int anomalySize) {
  bufferSize = circularSize;
  circularBuffer = new LogEntry[bufferSize];
  
  anomalyBufferSize = anomalySize;
  anomalyBuffer = new LogEntry[anomalyBufferSize];

  bufferIndex = 0;
  validSampleCount = 0;
  anomalyIndex = 0;
  sdCardAvailable = false;
  voltageThreshold = 5.0; // Default 5V threshold
  currentThreshold = 1.0; // Default 1A threshold
  lastAnomalyTime = 0;

  postAnomalyRemaining = 0;
  postAnomalySampleCount = 100; // default, can be tuned

  streamingEnabled = false;

  // streaming buffer defaults (fixed ring buffer)
  streamHead = 0; streamTail = 0; streamBufferLen = 0;
#ifdef LOW_MEMORY_DEVICE
  // Lower thresholds for low-memory devices (UNO)
  streamFlushThreshold = STREAM_BUFFER_CAP / 2; // bytes
  streamWriteRetries = 2;
#else
  streamFlushThreshold = STREAM_BUFFER_CAP / 2; // bytes
  streamWriteRetries = 3;
#endif

  // Attempt to load settings from EEPROM (post-anomaly count etc.)
  loadSettingsFromEEPROM();
}

DataLoggingManager::~DataLoggingManager() {
  delete[] circularBuffer;
  delete[] anomalyBuffer;
}

// --- Public Methods ---

bool DataLoggingManager::initialize() {
  if (SD.begin(SD_CS_PIN)) {
    sdCardAvailable = true;
    // Safety check: warn if buffer sizes are large for ATmega2560
#ifdef MAX_SAFE_LOG_ENTRIES
    if (bufferSize > MAX_SAFE_LOG_ENTRIES) {
      Serial.print("[WARN] Requested circular buffer size ");
      Serial.print(bufferSize);
      Serial.print(" > MAX_SAFE_LOG_ENTRIES (" );
      Serial.print(MAX_SAFE_LOG_ENTRIES);
      Serial.println("). Consider lowering to avoid SRAM exhaustion.");
    }
#endif
    return true;
  }
  sdCardAvailable = false;
  return false;
}

bool DataLoggingManager::flushStreamBuffer() {
  if (!sdCardAvailable || !activeStreamFile) return false;
  if (streamBufferLen == 0) return true;

  bool ok = false;
  int tries = streamWriteRetries;
  while (tries-- > 0) {
    // Write bytes from tail..head (watch wrap)
    int remaining = streamBufferLen;
    int pos = streamTail;
    while (remaining > 0) {
      int chunk = min(remaining, STREAM_BUFFER_CAP - pos);
      size_t written = activeStreamFile.write((const uint8_t*)&streamBuffer[pos], chunk);
      activeStreamFile.flush();
      if (written != (size_t)chunk) { break; }
      remaining -= chunk;
      pos = (pos + chunk) % STREAM_BUFFER_CAP;
    }
    if (remaining == 0) { ok = true; break; }
    // attempt to recover by rewinding
    activeStreamFile.rewind();
  }
  if (ok) {
    streamHead = streamTail = streamBufferLen = 0;
  } else {
    // Failover: stop streaming to avoid filling buffer with unsent data
    stopStreaming();
    Serial.println("[STREAM] Error: write failed, streaming stopped");
  }
  return ok;
}

void DataLoggingManager::logSample(const Measurement& measurement) {
  // 1. Add to the main circular buffer
  circularBuffer[bufferIndex].measurement = measurement;
  circularBuffer[bufferIndex].anomaly = false; // Assume not an anomaly initially
  circularBuffer[bufferIndex].timestamp = measurement.timestamp;

  // 2. If streaming is enabled, buffer to streamBuffer and commit in chunks for robustness
  if (streamingEnabled && sdCardAvailable) {
    // Build CSV line into buffer
    char lineBuf[128];
    int n = snprintf(lineBuf, sizeof(lineBuf), "%lu,%.6f,%.6f,0\n", measurement.timestamp, measurement.voltage, measurement.current);
    if (n > 0) {
      if (!appendToStreamBuffer(lineBuf, n)) {
        // append failed (buffer full and flush unsuccessful)
        Serial.println("[STREAM] Warning: stream buffer overflow, stopping streaming");
      }
    }
    // Flush if buffer exceeds threshold
    if (streamBufferLen >= streamFlushThreshold) {
      flushStreamBuffer();
    }
  }

  // 3. Check for anomaly
  if (detectAnomaly(measurement)) {
    // If it's an anomaly, log previous context and this sample
    logAnomaly(measurement, "Threshold exceeded");
    circularBuffer[bufferIndex].anomaly = true;
  }

  // 4. If we're capturing post-anomaly samples, copy to anomaly buffer
  if (postAnomalyRemaining > 0 && anomalyIndex < anomalyBufferSize) {
    anomalyBuffer[anomalyIndex].measurement = measurement;
    anomalyBuffer[anomalyIndex].anomaly = true;
    anomalyBuffer[anomalyIndex].timestamp = measurement.timestamp;
    anomalyIndex++;
    postAnomalyRemaining--;
  }

  // 5. Increment circular buffer index and valid count
  bufferIndex = (bufferIndex + 1) % bufferSize;
  if (validSampleCount < bufferSize) validSampleCount++;
}

bool DataLoggingManager::logAnomaly(const Measurement& measurement, const char* description) {
  // Prevent spamming anomalies (e.g., one per second max)
  if (millis() - lastAnomalyTime < 1000) {
    return false;
  }
  lastAnomalyTime = millis();

  // Copy previous valid samples (pre-anomaly context) into anomalyBuffer
  int toCopy = min(validSampleCount, anomalyBufferSize - anomalyIndex);
  int oldestIndex = (bufferIndex - validSampleCount + bufferSize) % bufferSize;
  for (int i = 0; i < toCopy; i++) {
    int idx = (oldestIndex + i) % bufferSize;
    anomalyBuffer[anomalyIndex].measurement = circularBuffer[idx].measurement;
    anomalyBuffer[anomalyIndex].anomaly = circularBuffer[idx].anomaly;
    anomalyBuffer[anomalyIndex].timestamp = circularBuffer[idx].timestamp;
    anomalyIndex++;
    if (anomalyIndex >= anomalyBufferSize) break;
  }

  // Add the anomaly sample itself (if space remains)
  if (anomalyIndex < anomalyBufferSize) {
    anomalyBuffer[anomalyIndex].measurement = measurement;
    anomalyBuffer[anomalyIndex].anomaly = true;
    anomalyBuffer[anomalyIndex].timestamp = measurement.timestamp;
    anomalyIndex++;
  }

  // If streaming is enabled, write anomaly context to stream buffer as well
  if (streamingEnabled && sdCardAvailable) {
    const char* hdr = "--- ANOMALY CONTEXT START ---\n";
    appendToStreamBuffer(hdr, strlen(hdr));
    int start = max(0, anomalyIndex - toCopy - 1);
    for (int i = start; i < anomalyIndex; i++) {
      char line[128];
      int n = snprintf(line, sizeof(line), "%lu,%.6f,%.6f,%d\n", anomalyBuffer[i].timestamp, anomalyBuffer[i].measurement.voltage, anomalyBuffer[i].measurement.current, anomalyBuffer[i].anomaly ? 1 : 0);
      if (n > 0) appendToStreamBuffer(line, n);
    }
    const char* ftr = "--- ANOMALY CONTEXT END ---\n";
    appendToStreamBuffer(ftr, strlen(ftr));
    // flush anomaly context immediately
    flushStreamBuffer();
  }

  // Schedule post-anomaly capture
  postAnomalyRemaining = min(postAnomalySampleCount, anomalyBufferSize - anomalyIndex);

  return true;
}

bool DataLoggingManager::detectAnomaly(const Measurement& measurement) {
  return (measurement.voltage > voltageThreshold || measurement.current > currentThreshold);
}

bool DataLoggingManager::appendToStreamBuffer(const char* data, int len) {
  if (!streamingEnabled || !sdCardAvailable) return false;
  if (len <= 0) return true;

  // If incoming data is larger than buffer capacity, fail
  if (len > STREAM_BUFFER_CAP) return false;

  // Ensure there is space; if not, attempt a flush
  if (streamBufferLen + len > STREAM_BUFFER_CAP) {
    if (!flushStreamBuffer()) return false;
  }

  // Append with wrap handling
  int spaceAtEnd = STREAM_BUFFER_CAP - streamHead;
  if (len <= spaceAtEnd) {
    memcpy(&streamBuffer[streamHead], data, len);
    streamHead = (streamHead + len) % STREAM_BUFFER_CAP;
  } else {
    memcpy(&streamBuffer[streamHead], data, spaceAtEnd);
    memcpy(&streamBuffer[0], data + spaceAtEnd, len - spaceAtEnd);
    streamHead = len - spaceAtEnd;
  }
  streamBufferLen += len;
  return true;
}

bool DataLoggingManager::exportToCSV(const char* filename) {
  return exportToCSVFiltered(filename, false, 0, 0);
}

bool DataLoggingManager::exportToCSVFiltered(const char* filename, bool anomaliesOnly, unsigned long fromTimestamp, unsigned long toTimestamp) {
  if (!sdCardAvailable) return false;

  File f = SD.open(filename, FILE_WRITE);
  if (!f) return false;

  f.println("timestamp_ms,voltage_V,current_A,is_anomaly");

  // Write filtered samples
  int actualCount = validSampleCount;
  int oldestIndex = (bufferIndex - actualCount + bufferSize) % bufferSize;
  for (int i = 0; i < actualCount; i++) {
    int index = (oldestIndex + i) % bufferSize;
    unsigned long ts = circularBuffer[index].timestamp;
    if ((fromTimestamp != 0 && ts < fromTimestamp) || (toTimestamp != 0 && ts > toTimestamp)) continue;
    if (anomaliesOnly && !circularBuffer[index].anomaly) continue;
    f.print(circularBuffer[index].timestamp);
    f.print(",");
    f.print(circularBuffer[index].measurement.voltage, 6);
    f.print(",");
    f.print(circularBuffer[index].measurement.current, 6);
    f.print(",");
    f.println(circularBuffer[index].anomaly ? "1" : "0");
  }

  // Optionally add anomaly section
  if (!anomaliesOnly && anomalyIndex > 0) {
    f.println("\n# Anomalies");
    for (int i = 0; i < anomalyIndex; i++) {
      unsigned long ts = anomalyBuffer[i].timestamp;
      if ((fromTimestamp != 0 && ts < fromTimestamp) || (toTimestamp != 0 && ts > toTimestamp)) continue;
      f.print(anomalyBuffer[i].timestamp);
      f.print(",");
      f.print(anomalyBuffer[i].measurement.voltage, 6);
      f.print(",");
      f.print(anomalyBuffer[i].measurement.current, 6);
      f.print(",");
      f.println(anomalyBuffer[i].anomaly ? "1" : "0");
    }
  }

  f.close();
  return true;
}

void DataLoggingManager::update() {
  // This could be used for time-based logging tasks in the future,
  // but for now, logging is driven by calls to logSample().
}

void DataLoggingManager::setPostAnomalySampleCount(int count) {
  postAnomalySampleCount = count;
}

int DataLoggingManager::getPostAnomalySampleCount() {
  return postAnomalySampleCount;
}

// ------------------- Settings persistence -------------------
#include <EEPROM.h>

#define EEPROM_SETTINGS_ADDR (EEPROM_CALIB_ADDR + EEPROM_CALIB_SIZE_BYTES)
#define EEPROM_SETTINGS_MAGIC 0x5E54
#define EEPROM_SETTINGS_VERSION 1

struct PersistedSettings {
  uint16_t magic;
  uint8_t version;
  uint16_t postAnomalySampleCount;
  uint16_t circularSize;
  uint16_t anomalySize;
  uint8_t reserved[8];
};

bool DataLoggingManager::saveSettingsToEEPROM() {
  PersistedSettings s;
  s.magic = EEPROM_SETTINGS_MAGIC;
  s.version = EEPROM_SETTINGS_VERSION;
  s.postAnomalySampleCount = postAnomalySampleCount;
  s.circularSize = bufferSize;
  s.anomalySize = anomalyBufferSize;
  EEPROM.put(EEPROM_SETTINGS_ADDR, s);
  return true;
}

bool DataLoggingManager::loadSettingsFromEEPROM() {
  PersistedSettings s;
  EEPROM.get(EEPROM_SETTINGS_ADDR, s);
  if (s.magic != EEPROM_SETTINGS_MAGIC || s.version != EEPROM_SETTINGS_VERSION) {
    return false;
  }
  postAnomalySampleCount = s.postAnomalySampleCount;
  // Do not automatically resize buffers here; require restart for safety, but store values for display
  return true;
}

bool DataLoggingManager::startStreaming(const char* filename) {
#ifdef LOW_MEMORY_DEVICE
  Serial.println("[STREAM] Streaming disabled on low-memory device (UNO) by default.");
  return false;
#endif
  if (!sdCardAvailable) return false;
  if (streamingEnabled && activeStreamFile) return true; // already streaming

  // Simple rotation: if filename exists, append _1, _2 ...
  char fname[64]; strncpy(fname, filename, sizeof(fname)-1); fname[sizeof(fname)-1] = '\0';
  if (SD.exists(fname)) {
    for (int i = 1; i < 100; i++) {
      snprintf(fname, sizeof(fname), "%s_%02d.csv", filename, i);
      if (!SD.exists(fname)) break;
    }
  }

  activeStreamFile = SD.open(fname, FILE_WRITE);
  if (!activeStreamFile) return false;

  // Write header if file is new or empty
  activeStreamFile.println("timestamp_ms,voltage_V,current_A,is_anomaly");
  activeStreamFile.flush();
  streamBuffer[0] = '\0'; streamBufferLen = 0; streamWriteRetries = 0;
  streamingEnabled = true;
  Serial.print("[STREAM] Streaming to SD file: "); Serial.println(fname);
  return true;
}

void DataLoggingManager::stopStreaming() {
  if (activeStreamFile) {
    // flush any remaining buffer first
    if (streamBufferLen > 0) flushStreamBuffer();
    activeStreamFile.flush();
    activeStreamFile.close();
  }
  streamingEnabled = false;
  streamBuffer[0] = '\0'; streamBufferLen = 0; streamWriteRetries = 0;
}

bool DataLoggingManager::isStreaming() {
  return streamingEnabled;
}

// --- Getters & Setters ---

bool DataLoggingManager::setAnomalyThresholds(float v_thresh, float c_thresh) {
  voltageThreshold = v_thresh;
  currentThreshold = c_thresh;
  return true;
}

LogEntry* DataLoggingManager::getRecentLogs(int count, int& actualCount) {
  actualCount = min(count, validSampleCount);
  // Note: returns pointer to internal circular buffer. Caller should be aware of circular ordering.
  return circularBuffer; 
}

LogEntry* DataLoggingManager::getAnomalyLogs(int& count) {
  count = anomalyIndex;
  return anomalyBuffer;
}

void DataLoggingManager::clearLogs() {
  bufferIndex = 0;
}

void DataLoggingManager::clearAnomalies() {
  anomalyIndex = 0;
}

bool DataLoggingManager::isSDCardAvailable() {
  return sdCardAvailable;
}

unsigned long DataLoggingManager::getLogCount() {
    return bufferSize; // Simplified, returns size of buffer
}

unsigned long DataLoggingManager::getAnomalyCount() {
    return anomalyIndex;
}

// exportToFile is not implemented in this pass for simplicity, focusing on CSV.
bool DataLoggingManager::exportToFile(const char* filename) {
    return false;
}
