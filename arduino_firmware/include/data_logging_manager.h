#ifndef DATA_LOGGING_MANAGER_H
#define DATA_LOGGING_MANAGER_H

#include <Arduino.h>
#include <SD.h>
#include "smart_oscilloscope.h"

class DataLoggingManager {
private:
  LogEntry* circularBuffer;
  int bufferSize;
  int bufferIndex;
  int validSampleCount; // number of valid samples in circular buffer

  LogEntry* anomalyBuffer;
  int anomalyBufferSize;
  int anomalyIndex;

  int postAnomalyRemaining; // how many post-anomaly samples still to capture
  int postAnomalySampleCount; // configurable number of post-anomaly samples to capture

  File logFile;
  File activeStreamFile;
  bool streamingEnabled;
  bool sdCardAvailable;
  float voltageThreshold;
  float currentThreshold;
  unsigned long lastAnomalyTime;

  // Streaming buffer & robustness (fixed-size ring buffer to avoid heap fragmentation)
#ifndef STREAM_BUFFER_CAP
#ifdef LOW_MEMORY_DEVICE
  #define STREAM_BUFFER_CAP 256
#else
  #define STREAM_BUFFER_CAP 512
#endif
#endif
  char streamBuffer[STREAM_BUFFER_CAP]; // ring buffer
  int streamHead; // next write position
  int streamTail; // read position for flush
  int streamBufferLen; // cached len
  int streamFlushThreshold; // bytes to trigger flush
  int streamWriteRetries;

  bool flushStreamBuffer();
  bool appendToStreamBuffer(const char* data, int len); // returns false if append failed (e.g., overflow)
  int getStreamBufferLen() const { return streamBufferLen; }

public:
  DataLoggingManager(int circularSize = 1000, int anomalySize = 100);
  ~DataLoggingManager();
  bool initialize();
  void logSample(const Measurement& measurement);
  bool logAnomaly(const Measurement& measurement, const char* description);
  LogEntry* getRecentLogs(int count, int& actualCount);
  LogEntry* getAnomalyLogs(int& count);
  bool exportToFile(const char* filename);
  bool exportToCSV(const char* filename);
  bool exportToCSVFiltered(const char* filename, bool anomaliesOnly = false, unsigned long fromTimestamp = 0, unsigned long toTimestamp = 0);
  bool setAnomalyThresholds(float voltageThreshold, float currentThreshold);
  void setPostAnomalySampleCount(int count);
  int getPostAnomalySampleCount();

  bool startStreaming(const char* filename); // Open/append to file and write streaming logs directly
  void stopStreaming();
  bool isStreaming();
  bool saveSettingsToEEPROM();
  bool loadSettingsFromEEPROM();

  void clearLogs();
  void clearAnomalies();
  bool isSDCardAvailable();
  unsigned long getLogCount();
  unsigned long getAnomalyCount();
  bool detectAnomaly(const Measurement& measurement);
  void update();
};

#endif // DATA_LOGGING_MANAGER_H