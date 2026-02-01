#ifndef TRANSPORT_H
#define TRANSPORT_H

#include <stdint.h>
#include <stddef.h>

// Abstract transport interface used by Comm layer.
// Implementations: SerialTransport (default), ESP32Transport (Wi‑Fi TCP server)

class Transport {
public:
  virtual ~Transport() {}
  virtual void begin(unsigned long baud = 115200) = 0; // for Serial transport
  virtual void poll() = 0; // periodic maintenance (accept clients, etc.)
  virtual int available() = 0;
  virtual int read() = 0; // returns -1 on no data
  virtual int peek() = 0; // peek next byte, -1 if none
  virtual size_t write(const uint8_t* buf, size_t len) = 0;
};

#endif // TRANSPORT_H
