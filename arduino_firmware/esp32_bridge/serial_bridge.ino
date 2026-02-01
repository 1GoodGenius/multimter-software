#include <WiFi.h>
#if defined(ARDUINO_ARCH_ESP32)
#include <WiFiClientSecure.h>
#include <WiFiServerSecure.h>
#endif

// Simple ESP32 Serial-to-TCP bridge (single client)
// Configure SSID/PSK as desired, or modify to use STA mode

const char* ssid = "Multimeter-Bridge";
const char* password = "multimeter";
const uint16_t port = 5000;

// Toggle TLS support (set to 1 to enable server-side TLS with embedded test cert)
#define TLS_ENABLED 0
// Toggle mutual TLS (client cert) verification. Requires CA cert in certs.h and
// an ESP32 core that supports setting the CA for client verification.
#define MTLS_ENABLED 0

#if TLS_ENABLED && defined(ARDUINO_ARCH_ESP32)
#include "certs.h" // provides TEST_CERT_PEM, TEST_PRIVKEY_PEM, optional TEST_CA_PEM
WiFiServerSecure server(port);
WiFiClientSecure client;
#else
WiFiServer server(port);
WiFiClient client;
#endif

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 Serial Bridge starting...");

  WiFi.softAP(ssid, password);
  IPAddress ip = WiFi.softAPIP();
  Serial.printf("AP started. IP: %s, port %u\n", ip.toString().c_str(), port);

#if TLS_ENABLED && defined(ARDUINO_ARCH_ESP32)
  // Load test certificate and key (for demonstration only)
  if (server.setCertificate(TEST_CERT_PEM, TEST_PRIVKEY_PEM)) {
    Serial.println("[TLS] Certificate loaded");
  } else {
    Serial.println("[TLS] Failed to load certificate");
  }
#if MTLS_ENABLED
  // If mutual TLS is desired, the bridge can optionally verify client certs.
  // Place CA certificate PEM in certs.h as TEST_CA_PEM and call setClientCACert()/setCACert
  // depending on the ESP32 core API. Some cores expose setCACert() on WiFiClientSecure or server APIs.
  #ifdef TEST_CA_PEM
    // NOTE: The function name for loading CA into server depends on the core. If your core
    // supports it, implement: server.setClientCACert(TEST_CA_PEM) or similar.
    Serial.println("[TLS] MTLS enabled: ensure TEST_CA_PEM is populated in certs.h and update source to call server.setClientCACert(TEST_CA_PEM)");
  #else
    Serial.println("[TLS] MTLS enabled but TEST_CA_PEM not provided in certs.h");
  #endif
#endif
  server.begin();
#else
  server.begin();
#endif
}

void loop() {
#if TLS_ENABLED && defined(ARDUINO_ARCH_ESP32)
  if (!client || !client.connected()) {
    client = server.available();
    if (client) Serial.println("Client connected (TLS)");
  }
#else
  if (!client || !client.connected()) {
    client = server.available();
    if (client) {
      Serial.println("Client connected");
    }
  }
#endif

  // forward from client -> Serial
  if (client && client.connected() && client.available()) {
    while (client.available()) {
      int b = client.read();
      Serial.write((uint8_t)b);
    }
  }

  // forward from Serial -> client
  while (Serial.available()) {
    int b = Serial.read();
    if (client && client.connected()) client.write((uint8_t)b);
  }

  delay(1);
}
