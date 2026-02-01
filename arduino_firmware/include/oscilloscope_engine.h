#ifndef OSCILLOSCOPE_ENGINE_H
#define OSCILLOSCOPE_ENGINE_H

#include <Arduino.h>
#include "smart_oscilloscope.h"

class OscilloscopeEngine {
private:
  WaveformSample* waveformBuffer;
  int bufferSize;
  int bufferIndex;
  bool capturing;
  bool triggerEnabled;
  float triggerLevel;
  TriggerEdge triggerEdge;
  bool triggerFired;
  float zoomFactor;
  int sampleRate;
  unsigned long lastSampleTime;

  // Bookkeeping for buffer content
  int validSampleCount;
  int bufferStartIndex; // index of oldest valid sample
  float lastSampleValue; // for edge detection
  
public:
  OscilloscopeEngine(int size = 1024);
  ~OscilloscopeEngine();
  bool initialize();
  void startCapture();
  void stopCapture();
  void addSample(float value, unsigned long timestamp);
  void setTrigger(float level, TriggerEdge edge = TRIGGER_RISING);
  void enableTrigger(bool enable);
  WaveformSample* getWaveformData(int& count, int& startIndex);
  int getValidSampleCount();
  void setZoomFactor(float factor);
  float getZoomFactor();
  int getSampleRate();
  void setSampleRate(int rate);
  int getBufferSize();
  void clearBuffer();
  bool isCapturing();
  bool checkTrigger(float value);
  void update();
};

#endif // OSCILLOSCOPE_ENGINE_H