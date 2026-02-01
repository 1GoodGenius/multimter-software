# File Transfer Testing Guide

This guide provides step-by-step instructions to validate the file transfer implementation end-to-end.

## Prerequisites

- **Hardware:** Arduino Mega with USB cable
- **Software:** Python 3.7+, `tools/` directory with helper scripts
- **Firmware:** Point 2 communication manager compiled and flashed

## Part 1: Firmware Flashing

### Option A: Using Arduino IDE

1. Open `arduino_firmware/src/main.cpp` in Arduino IDE
2. Select Board: **Arduino Mega or Mega 2560**
3. Select Port: **COM3** (or your USB port)
4. Click **Upload**
5. Wait for "Done uploading" message

### Option B: Using avrdude Command Line

```bash
cd arduino_firmware

# Compile
avr-g++ -mmcu=atmega2560 -DF_CPU=16000000UL -Os \
  -I./include src/*.cpp src/engines/*.cpp \
  -o build/firmware.elf

# Convert to HEX
avr-objcopy -O ihex build/firmware.elf build/firmware.hex

# Flash
avrdude -p m2560 -c wiring -P COM3 -b 115200 -D \
  -U flash:w:build/firmware.hex:i
```

## Part 2: Basic Communication Test (HELLO)

### Step 1: Open Terminal and Run HELLO Test

```bash
cd tools

python test_e2e_file_transfer.py \
  --port COM3 \
  --hello
```

**Expected Output:**
```
Testing HELLO on COM3...
Sending HELLO frame...
✓ HELLO response received (version: 1, flags: 0x00)
```

**If FAILED:**
- Ensure device is connected and powered
- Check baud rate (should be 9600 by default in firmware)
- Use `python -m serial.tools.list_ports` to verify COM port
- Check device manager for "Arduino Mega 2560" (not "Unknown Device")

---

## Part 3: Authentication Test

### Step 2: Run AUTH Test

You can authenticate with either the legacy plaintext token or the new HMAC-based timestamped AUTH.

Plaintext token example:

```bash
python test_e2e_file_transfer.py \
  --port COM3 \
  --auth \
  --token "test_token"
```

HMAC example (provide hex key, host will send timestamp+HMAC; device must have key provisioned via `AUTH_SETKEY`):

```bash
python test_e2e_file_transfer.py \
  --port COM3 \
  --auth \
  --hmac-key "001122334455..."
```

**Expected Output:**
```
Testing AUTH on COM3...
Sending AUTH frame with token: test_token...
✓ AUTH accepted (ACK received)
```

**If FAILED (ACK timeout):**
- Check that `#define AUTH_ENABLED 1` in `communication_manager.h`
- Verify token matches hardcoded token in `communication_manager.cpp` (default: "test_token")
- Monitor serial output with a terminal to see device-side logs

**If FAILED (NACK received):**
- Token mismatch
- Ensure firmware was recompiled with latest communication_manager.cpp

---

## Part 4: File Transfer Test

### Step 3: Prepare a Test File

Create a small test file (e.g., 2 KB):

```bash
# Linux/Mac
dd if=/dev/urandom of=test_file.bin bs=1024 count=2

# Windows PowerShell
$buffer = [byte[]]::new(2048)
(New-Object Random).NextBytes($buffer)
[System.IO.File]::WriteAllBytes('test_file.bin', $buffer)
```

### Step 4: Run File Transfer Test

```bash
python test_e2e_file_transfer.py \
  --port COM3 \
  --file test_file.bin \
  --token "test_token"
```

**Expected Output:**
```
Testing FILE_TRANSFER on COM3...
Sending FILE_TRANSFER_START frame...
✓ FILE_TRANSFER_START ACK received

Sending chunk 1/4 (512 bytes)...
✓ Chunk 1 ACK received

Sending chunk 2/4 (512 bytes)...
✓ Chunk 2 ACK received

Sending chunk 3/4 (512 bytes)...
✓ Chunk 3 ACK received

Sending chunk 4/4 (512 bytes)...
✓ Chunk 4 ACK received

Sending FILE_TRANSFER_END frame...
✓ FILE_TRANSFER_END ACK received

✓ File transfer complete
```

**If FAILED (partial chunks):**
- Device may have insufficient RAM for buffer
- Reduce chunk size in `tools/file_transfer.py`: change `CHUNK_SIZE = 512` to `CHUNK_SIZE = 256`
- Recompile firmware with `#define FILE_TRANSFER_CHUNK_SIZE 256` in `communication_manager.h`

**If FAILED (timeout on some chunk):**
- Serial port may have interference
- Try different USB cable or port
- Add `--retry 5` flag to test harness to increase retry count

---

## Part 5: Full End-to-End Validation

Run all three tests in sequence:

```bash
python test_e2e_file_transfer.py \
  --port COM3 \
  --hello \
  --auth \
  --file test_file.bin \
  --token "test_token" \
  --verbose
```

**Expected Output:**
```
Testing HELLO on COM3...
✓ HELLO response received (version: 1, flags: 0x00)

Testing AUTH on COM3...
✓ AUTH accepted (ACK received)

Testing FILE_TRANSFER on COM3...
Sending FILE_TRANSFER_START frame...
✓ FILE_TRANSFER_START ACK received
...
✓ File transfer complete

========================================
✓ ALL TESTS PASSED
========================================
```

---

## Part 6: Advanced Testing

### Test with Real Firmware Update

If you have a secondary firmware build (e.g., `firmware_v2.hex`):

```bash
# Convert HEX to BIN if needed
avr-objcopy -I ihex -O binary firmware_v2.hex firmware_v2.bin

# Send via file transfer
python tools/file_transfer.py \
  --serial COM3 \
  --send firmware_v2.bin \
  --token "test_token"
```

### Test with TCP Bridge (ESP32)

If using ESP32 serial bridge:

```bash
# First, flash ESP32 with esp32_bridge/serial_bridge.ino
# ESP32 creates WiFi network "Multimeter-Bridge"

python test_e2e_file_transfer.py \
  --tcp 192.168.4.1:5000 \
  --hello \
  --auth \
  --token "test_token"
```

### Test Robustness

Test with packet loss or noise simulation:

```bash
# Use tc (traffic control) on Linux to introduce packet loss
tc qdisc add dev eth0 root netem loss 5%

python test_e2e_file_transfer.py \
  --port /dev/ttyUSB0 \
  --file test_file.bin \
  --token "test_token" \
  --retry 10
```

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Port opens but no response | Firmware not flashed or baud rate mismatch | Re-flash firmware; check baud rate in main.cpp |
| "Frame timeout" | Device not responding in time | Check device logs; increase `--timeout 5` flag |
| "CRC mismatch" | Serial corruption or buffer overflow | Reduce `CHUNK_SIZE`; check cable quality |
| "AUTH NACK" | Token mismatch | Verify token in firmware matches CLI arg |
| "FILE_TRANSFER hangs on chunk N" | Device RAM exhausted | Reduce chunk size or file size |
| Python ImportError: no module 'serial' | pyserial not installed | Run `pip install pyserial` |

---

## Expected Test Times

| Test | Time | Notes |
|------|------|-------|
| HELLO | < 1 sec | Instant response |
| AUTH | < 1 sec | Token validation |
| FILE_TRANSFER (2 KB) | 2–5 sec | Depends on chunk size and retry |
| Full E2E | 5–10 sec | All three tests |

---

## Next Steps

After successful validation:

1. ✅ Firmware is working and responsive
2. ✅ Authentication is enforced
3. ✅ File transfer is reliable
4. **Next:** See [USAGE_GUIDE.md](USAGE_GUIDE.md) for integrating with your application
5. **Security:** Review [SECURITY_AND_OTA.md](SECURITY_AND_OTA.md) for production hardening

---

For detailed protocol information, see [PROTOCOL.md](PROTOCOL.md).
