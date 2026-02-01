#ifndef ARDUINO_MULTIMETER_H
#define ARDUINO_MULTIMETER_H

#include <Arduino.h>
#include <HardwareSerial.h>

class ArduinoMultimeter {
public:
    ArduinoMultimeter(HardwareSerial& serial = Serial);
    ~ArduinoMultimeter();
    
    // Initialize the multimeter communication
    bool begin(long baudRate = 9600);
    
    // Read measurements
    float readVoltage();
    float readCurrent();
    float readResistance();
    
    // Get measurement status
    bool isDataAvailable();
    bool isConnected();
    
    // Control operations
    void sendCommand(const String& command);
    String getResponse();
    void clearBuffer();

private:
    HardwareSerial& _serial;
    bool _initialized;
    String _buffer;
    
    // Helper methods
    float parseValue(const String& data, const String& type);
    bool waitForResponse(unsigned long timeout = 1000);
};

#endif