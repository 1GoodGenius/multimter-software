# Arduino Multimeter Software

Professional multimeter software with GUI for measuring voltage, current, resistance, and temperature using Arduino analog pins.

## Features

- **Real-time Arduino Integration**: Connect Arduino Uno/Nano for actual measurements
- **Multiple Measurement Modes**: Voltage, Current, Resistance, Temperature, Continuity testing
- **Professional GUI**: Large digital displays, analog-style graphs, and data logging
- **Data Export**: Export measurements to CSV format
- **Auto-ranging**: Automatic range selection or manual range control
- **Calibration Support**: Built-in calibration and zero offset features
- **Live Graphs**: Real-time visualization of measurement trends
- **Comprehensive Logging**: Timestamped measurement history

## Hardware Requirements

### Arduino Setup
- Arduino Uno or Nano
- Components:
  - ACS712 current sensor (for current measurement)
  - LM35 temperature sensor (for temperature measurement)
  - 10kΩ resistor (for resistance measurement voltage divider)
  - Voltage divider (30V max to Arduino 5V)
  - Breadboard and connecting wires

### Wiring Diagram
```
Arduino Connections:
A0 → Voltage divider (0-30V input)
A1 → ACS712 current sensor output
A2 → Resistance measurement divider
A3 → LM35 temperature sensor
D2 → Continuity test pin (with pullup)

ACS712 Current Sensor:
VCC → 5V
GND → GND
OUT → A1
IP+ → Current path (positive)
IP- → Current path (negative)

LM35 Temperature Sensor:
VCC → 5V
GND → GND
OUT → A3

Voltage Divider (for 0-30V measurement):
Vin (0-30V) → 10kΩ resistor → A0 → 2kΩ resistor → GND
```

## Software Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Upload Arduino Firmware
1. Open Arduino IDE
2. Load `arduino_multimeter.ino`
3. Select your Arduino board and port
4. Upload the firmware

### 2. Run the Python GUI
```bash
python multimeter_software.py
```

### 3. Connect and Use
1. Click "Refresh Ports" to detect Arduino
2. Select your Arduino port from the dropdown
3. Click "Connect" to establish connection
4. Select measurement mode (Voltage, Current, Resistance, etc.)
5. View real-time measurements on the display

## Measurement Capabilities

### Voltage Measurement
- Range: 0-30V DC (with voltage divider)
- Resolution: 0.001V
- Auto-ranging support

### Current Measurement
- Range: ±5A (with ACS712-5A sensor)
- Resolution: 0.000001A
- Bidirectional measurement

### Resistance Measurement
- Range: 10Ω - 1MΩ
- Uses voltage divider method
- 10kΩ reference resistor required

### Temperature Measurement
- Range: 0-100°C
- Resolution: 0.1°C
- Uses LM35 sensor

### Continuity Testing
- Visual and serial indication
- Threshold: < 50Ω
- Audio beep output

## GUI Features

### Main Display Tab
- Large LCD-style displays for each measurement type
- Real-time status indicators
- Connection status

### Graphs Tab
- Live plotting of voltage, current, and resistance
- Historical trend visualization
- Auto-scaling graphs

### Data Log Tab
- Timestamped measurement records
- Export to CSV functionality
- Clear log option

## Calibration

### Voltage Calibration
1. Apply known reference voltage (e.g., 5V from Arduino)
2. Click "Calibrate" button
3. Enter the known voltage value
4. Software automatically calculates calibration factor

### Current Zero Offset
1. Disconnect any load from current sensor
2. Click "Zero Offset" button
3. Software measures and compensates for zero-current offset

## Serial Communication Protocol

### Commands from GUI to Arduino:
- `MODE:voltage` - Set voltage measurement mode
- `MODE:current` - Set current measurement mode
- `MODE:resistance` - Set resistance measurement mode
- `MODE:temperature` - Set temperature measurement mode
- `MODE:continuity` - Set continuity test mode
- `CAL:5.0` - Calibrate with 5V reference
- `ZERO` - Zero current offset
- `RANGE:auto` - Enable auto-ranging
- `STATUS` - Show Arduino status

### Data from Arduino to GUI:
Format: `V:volts,I:amps,R:ohms,T:celsius`
Example: `V:5.123,I:0.123456,R:1000.0,T:25.5`

## Troubleshooting

### Connection Issues
- Ensure Arduino is properly connected via USB
- Check correct COM port selection
- Verify Arduino firmware is uploaded successfully
- Try pressing Arduino reset button

### Measurement Issues
- Check wiring connections
- Verify component specifications
- Calibrate measurements regularly
- Ensure proper voltage divider ratios

### Software Issues
- Install all required Python dependencies
- Run as administrator if port access issues occur
- Check for conflicting serial port usage

## Project layout

This repository contains firmware, PC software, mobile app code and static assets. For clarity and maintainability we recommend the structure below and have started adding docs and examples to help migrate files:

- `arduino_firmware/` or `firmware/` – Arduino sketches, `include/`, and `src/` for embedded code
- `pc_software/` – Host/desktop Python applications, GUI code, and CLI tools
  - `pc_software/desktop/` – (proposed) Desktop scripts and GUI entry points
  - `pc_software/` – shared host helpers and the `bluetooth.py` module
- `mobile_app/` – Phone app sources and assets
- `tools/` – Small host helper scripts (serial bridge, comm helper, tests)
- `docs/` – Documentation and how-tos (BRIDGING, AUTH_HARDENING, TESTING, etc.)
- `static/`, `templates/` – Web/static assets

## Files

- `multimeter_software.py` - Main GUI application (proposed move to `pc_software/desktop/`)
- `arduino_multimeter.ino` - Arduino firmware (kept in `arduino_firmware/`)
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Technical Specifications

### Arduino Requirements
- Microcontroller: ATmega328P (Uno/Nano)
- Clock Speed: 16MHz
- ADC Resolution: 10-bit (0-1023)
- Serial Speed: 9600 baud

### Software Requirements
- Python 3.7+
- PyQt5 (GUI framework)
- pyserial (Arduino communication)
- NumPy (data processing)

### Measurement Accuracy
- Voltage: ±1% (after calibration)
- Current: ±2% (with ACS712 sensor)
- Resistance: ±5% (voltage divider method)
- Temperature: ±1°C (LM35 sensor)

## Safety Notes

- Never exceed 30V on voltage input
- Use proper current sensor rating
- Ensure proper insulation of high-voltage connections
- Double-check wiring before powering on
- Use appropriate safety equipment when working with electricity

## Firmware updates (Point 1)

Recent firmware improvements (Measurement, Oscilloscope, Calculator, Data Logging, UI):
- Non-blocking calibration wizard with progress and save-to-profile flow
- EEPROM-backed profile save/load/delete/list plus on-screen profile name editor
- SD chunked streaming with file rotation and write retries (streaming to CSV)
- Pre/post-anomaly capture and anomaly context export
- Oscilloscope decimated rendering (min/max per pixel) to preserve peaks and reduce CPU
- Simple on-screen measurements (Vpp, RMS) overlays
- Auto-ranging hysteresis, cooldown and EWMA smoothing to prevent chattering
- Overload callback and on-screen overload indicator
- Integration test runner with optional CSV streaming from SD

## License

This project is provided as-is for educational use and still under building. Use at your own risk.

---

## Point 2: Communication Manager (scaffold)

Work started on a lightweight Communication Manager to provide a framed serial protocol and handler registration. Goals for Point 2:
- Reliable framed protocol (CRC validated)
- Command/response and event streaming
- Transport abstraction (Serial / BLE / Wi‑Fi)
- Acknowledgements, retries, and versioned commands
- Small footprint for low-memory targets (configurable)

A scaffold is available: `include/communication_manager.h` and `src/communication_manager.cpp` with basic frame receive/send and handler registration.

Next steps: integrate command handlers (profile export/import, test control, calibration trigger), add CLI->frame translation and implement a minimal host-side helper.