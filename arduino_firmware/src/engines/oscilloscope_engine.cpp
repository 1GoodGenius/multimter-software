#include "oscilloscope_engine.h"

OscilloscopeEngine::OscilloscopeEngine(int size) {
  bufferSize = size;
  waveformBuffer = new WaveformSample[bufferSize];
  bufferIndex = 0;
  capturing = false;
  triggerEnabled = false;
  triggerLevel = 1.65; // Default trigger level (mid-scale)
  triggerEdge = TRIGGER_RISING;
  triggerFired = false;
  zoomFactor = 1.0;
  sampleRate = 1000; // Default 1kHz sample rate
  lastSampleTime = 0;

  validSampleCount = 0;
  bufferStartIndex = 0;
  lastSampleValue = 0.0f;
}

OscilloscopeEngine::~OscilloscopeEngine() {
  delete[] waveformBuffer;
}

bool OscilloscopeEngine::initialize() {
  clearBuffer();
  return true;
}

void OscilloscopeEngine::startCapture() {
  capturing = true;
  triggerFired = false;
  bufferIndex = 0;
  validSampleCount = 0;
  bufferStartIndex = 0;
  lastSampleTime = micros();
}

void OscilloscopeEngine::stopCapture() {
  capturing = false;
}

void OscilloscopeEngine::addSample(float value, unsigned long timestamp) {
  if (!capturing) return;

  // Check trigger condition if enabled
  if (triggerEnabled && !triggerFired) {
    if (checkTrigger(value)) {
      triggerFired = true;
      // Reset buffer to start capturing from trigger point
      bufferIndex = 0;
      validSampleCount = 0;
      bufferStartIndex = 0;
    } else {
      return; // Don't store samples until trigger fires
    }
  }

  // Store sample in buffer (store raw value; apply zoom at render time)
  waveformBuffer[bufferIndex].value = value;
  waveformBuffer[bufferIndex].timestamp = timestamp;

  bufferIndex++;
  if (bufferIndex >= bufferSize) {
    bufferIndex = 0; // Circular buffer
  }

  if (validSampleCount < bufferSize) {
    validSampleCount++;
  } else {
    // Full buffer: move start index forward so data stays chronological
    bufferStartIndex = (bufferIndex + 1) % bufferSize; // oldest = next index after write
  }
}

void OscilloscopeEngine::setTrigger(float level, TriggerEdge edge) {
  triggerLevel = level;
  triggerEdge = edge;
}

void OscilloscopeEngine::enableTrigger(bool enable) {
  triggerEnabled = enable;
  triggerFired = false;
}

WaveformSample* OscilloscopeEngine::getWaveformData(int& count, int& startIndex) {
  count = validSampleCount;
  startIndex = bufferStartIndex;
  return waveformBuffer;
}

int OscilloscopeEngine::getValidSampleCount() {
  return validSampleCount;
}

void OscilloscopeEngine::setZoomFactor(float factor) {
  if (factor > 0.1 && factor < 100.0) {
    zoomFactor = factor;
  }
}

float OscilloscopeEngine::getZoomFactor() {
  return zoomFactor;
}

int OscilloscopeEngine::getSampleRate() {
  return sampleRate;
}

void OscilloscopeEngine::setSampleRate(int rate) {
  if (rate > 100 && rate < 100000) { // Valid range: 100Hz to 100kHz
    sampleRate = rate;
  }
}

void OscilloscopeEngine::clearBuffer() {
  for (int i = 0; i < bufferSize; i++) {
    waveformBuffer[i].value = 0.0;
    waveformBuffer[i].timestamp = 0;
  }
  bufferIndex = 0;
  validSampleCount = 0;
  bufferStartIndex = 0;
}

bool OscilloscopeEngine::isCapturing() {
  return capturing;
}

bool OscilloscopeEngine::checkTrigger(float value) {
  bool triggered = false;

  switch (triggerEdge) {
    case TRIGGER_RISING:
      triggered = (lastSampleValue <= triggerLevel && value > triggerLevel);
      break;
    case TRIGGER_FALLING:
      triggered = (lastSampleValue >= triggerLevel && value < triggerLevel);
      break;
    case TRIGGER_BOTH:
      triggered = ((lastSampleValue <= triggerLevel && value > triggerLevel) ||
                   (lastSampleValue >= triggerLevel && value < triggerLevel));
      break;
  }

  lastSampleValue = value;
  return triggered;
}

int OscilloscopeEngine::getBufferSize() { return bufferSize; }

void OscilloscopeEngine::update() {
  if (!capturing) return;

  unsigned long currentTime = micros();
  unsigned long sampleInterval = 1000000 / sampleRate; // microseconds between samples

  if (currentTime - lastSampleTime >= sampleInterval) {
    // This should be called with actual measurement data
    // addSample(measurementValue, currentTime);
    lastSampleTime = currentTime;
  }
}