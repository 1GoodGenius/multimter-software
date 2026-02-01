#if defined(ESP32)

#include "transport.h"
#include <WiFi.h>
#include <WiFiClient.h>
#include <WiFiAP.h>

class ESP32Transport : public Transport {
public:
  ESP32Transport() : server(nullptr), client() {}
  bool beginAP(const char* ssid, const char* pass, uint16_t port) {
    // Start soft AP
    WiFi.softAP(ssid, pass);
    delay(500);
    server = new WiFiServer(port);
    server->begin();
    Serial.print("[WiFi] AP started: "); Serial.println(ssid);
    Serial.print("[WiFi] IP: "); Serial.println(WiFi.softAPIP());
    return true;
  }
  void begin(unsigned long baud = 115200) override {
    // no-op; beginAP must be used to configure AP
  }
  void poll() override {
    if (!server) return;
    if (!client || !client.connected()) {
      if (server->hasClient()) {
        WiFiClient c = server->available();
        if (c) {
          client = c;
          Serial.println("[WiFi] Client connected");
        }
      }
    }
  }
  int available() override { if (client && client.connected()) return client.available(); return 0; }
  int read() override { if (client && client.connected()) return client.read(); return -1; }
  int peek() override { if (client && client.connected()) return client.peek(); return -1; }
  size_t write(const uint8_t* buf, size_t len) override { if (client && client.connected()) return client.write(buf, len); return 0; }
private:
  WiFiServer* server;
  WiFiClient client;
};

#endif // ESP32
