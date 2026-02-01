# Complete Usage Guide: Auth + Profile Export/Import + File Transfer

This guide demonstrates real-world workflows combining authentication, profile management, and file transfer capabilities.

## Workflow 1: Initial Device Setup & Authentication

### Scenario
You have a freshly flashed Arduino Mega and need to establish secure communication.

### Step 1: Send HELLO

```python
#!/usr/bin/env python3
"""Initialize device and authenticate"""

from tools.comm_helper import SerialConnection

# Connect to device
conn = SerialConnection(port="/dev/ttyUSB0", baudrate=9600)

# Send HELLO
hello_response = conn.send_hello()
print(f"Device version: {hello_response['version']}")
print(f"Device flags: {hello_response['flags']}")

# Expected output:
# Device version: 1
# Device flags: 0x00
```

### Step 2: Authenticate

```python
# Send AUTH with token
token = "test_token"
auth_response = conn.send_auth(token)

if auth_response['ack']:
    print("✓ Authentication successful")
else:
    print("✗ Authentication failed")
    exit(1)
```

### Step 3: Query Device Capabilities

```python
# Optional: Device can report supported profiles
# (This requires custom frame type CAPS_QUERY; shown for completeness)
"""
GET /api/device/capabilities
{
  "profiles_supported": ["temperature", "voltage", "current"],
  "max_file_size": 65536,
  "chunk_size": 512,
  "auth_required": true
}
"""
```

---

## Workflow 2: Export Current Measurement Profile

### Scenario
Device has been running with optimal settings for a specific measurement type.
You want to save this profile for reuse.

### Step 1: Request Profile Export

Using the **PROFILE_EXPORT** frame (type 0x10):

```python
"""
Frame structure for PROFILE_EXPORT request:
[0xAA][LEN_H][LEN_L][0x10][PAYLOAD][CRC16]

Payload:
  - 1 byte: profile_type (0x01=temperature, 0x02=voltage, etc.)
  - Optional: reserved bytes
"""

def send_profile_export(conn, profile_type):
    """Request device to export a measurement profile"""
    frame = conn.build_frame(
        frame_type=0x10,  # PROFILE_EXPORT
        payload=bytes([profile_type])
    )
    conn.write(frame)
    response = conn.read_ack(timeout=2.0)
    return response

# Request voltage measurement profile
profile_export = send_profile_export(conn, profile_type=0x02)
print(f"Profile export request sent: {profile_export['ack']}")
```

### Step 2: Receive Profile Data

Device responds with profile payload (typically 64–256 bytes containing settings):

```python
"""
Frame structure for PROFILE_EXPORT response:
[0xAA][LEN_H][LEN_L][0x10][PROFILE_DATA...][CRC16]

Profile data (example):
  - 2 bytes: range (0–4095)
  - 2 bytes: filter_coeff (EWMA alpha)
  - 1 byte: autorange_enabled (0/1)
  - ... (device-specific fields)
"""

def receive_profile_data(conn):
    """Receive exported profile data"""
    frame = conn.read_frame(timeout=2.0)
    if frame['type'] == 0x10:
        return frame['payload']
    return None

profile_data = receive_profile_data(conn)
print(f"Profile data received: {len(profile_data)} bytes")

# Save to file
with open("voltage_profile.bin", "wb") as f:
    f.write(profile_data)
print("Profile saved to voltage_profile.bin")
```

---

## Workflow 3: Import Profile From File

### Scenario
You have a previously saved profile and want to load it onto a device.

### Step 1: Read Profile File

```python
with open("voltage_profile.bin", "rb") as f:
    profile_data = f.read()

print(f"Profile size: {len(profile_data)} bytes")
```

### Step 2: Send Profile Import Request

Using the **PROFILE_IMPORT** frame (type 0x11):

```python
"""
Frame structure for PROFILE_IMPORT:
[0xAA][LEN_H][LEN_L][0x11][PROFILE_DATA...][CRC16]

Payload:
  - 1 byte: profile_type (must match export type)
  - N bytes: profile data
"""

def send_profile_import(conn, profile_type, profile_data):
    """Send profile to device"""
    payload = bytes([profile_type]) + profile_data
    frame = conn.build_frame(
        frame_type=0x11,  # PROFILE_IMPORT
        payload=payload
    )
    conn.write(frame)
    response = conn.read_ack(timeout=2.0)
    return response

response = send_profile_import(conn, profile_type=0x02, profile_data=profile_data)

if response['ack']:
    print("✓ Profile imported successfully")
else:
    print("✗ Profile import failed")
```

### Step 3: Verify Profile

```python
# Optional: Query device to confirm new settings
def verify_profile(conn, profile_type):
    """Re-export profile to verify import was successful"""
    exported = send_profile_export(conn, profile_type)
    with open("voltage_profile_verify.bin", "wb") as f:
        f.write(exported)
    return exported == profile_data

if verify_profile(conn, 0x02):
    print("✓ Profile verification passed")
```

---

## Workflow 4: File Transfer (Firmware / Configuration)

### Scenario
You want to send a 4 KB configuration file or firmware update to the device.

### Step 1: Prepare File

```python
import hashlib

file_path = "config.bin"  # or firmware.bin

with open(file_path, "rb") as f:
    file_data = f.read()

file_hash = hashlib.sha256(file_data).hexdigest()
print(f"File size: {len(file_data)} bytes")
print(f"SHA256: {file_hash}")
```

### Step 2: Initiate File Transfer

Using **FILE_TRANSFER_START** (type 0x30):

```python
"""
Frame structure for FILE_TRANSFER_START:
[0xAA][LEN_H][LEN_L][0x30][PAYLOAD][CRC16]

Payload:
  - 2 bytes: file_size (BE)
  - 1 byte: file_type (0x01=config, 0x02=firmware, etc.)
  - 32 bytes: SHA256 hash (optional, for verification)
"""

def send_file_start(conn, file_size, file_type, file_hash=None):
    """Initiate file transfer"""
    payload = (
        file_size.to_bytes(2, 'big') +
        bytes([file_type])
    )
    if file_hash:
        payload += bytes.fromhex(file_hash)
    
    frame = conn.build_frame(frame_type=0x30, payload=payload)
    conn.write_with_ack(frame, timeout=2.0)
    return True

send_file_start(
    conn,
    file_size=len(file_data),
    file_type=0x01,  # config
    file_hash=file_hash
)
print("✓ File transfer started")
```

### Step 3: Send File in Chunks

Using **FILE_TRANSFER_CHUNK** (type 0x31):

```python
"""
Frame structure for FILE_TRANSFER_CHUNK:
[0xAA][LEN_H][LEN_L][0x31][PAYLOAD][CRC16]

Payload:
  - 2 bytes: chunk_index (BE)
  - N bytes: chunk_data (up to 512 bytes recommended)
"""

CHUNK_SIZE = 512

def send_file_chunks(conn, file_data, chunk_size=512):
    """Send file in chunks with ACK for each"""
    num_chunks = (len(file_data) + chunk_size - 1) // chunk_size
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, len(file_data))
        chunk = file_data[start:end]
        
        payload = i.to_bytes(2, 'big') + chunk
        frame = conn.build_frame(frame_type=0x31, payload=payload)
        
        conn.write_with_ack(frame, timeout=2.0, retries=3)
        print(f"  Chunk {i+1}/{num_chunks} sent ({len(chunk)} bytes)")

send_file_chunks(conn, file_data)
print("✓ All chunks sent")
```

### Step 4: Complete File Transfer

Using **FILE_TRANSFER_END** (type 0x32):

```python
"""
Frame structure for FILE_TRANSFER_END:
[0xAA][LEN_H][LEN_L][0x32][PAYLOAD][CRC16]

Payload:
  - 32 bytes: SHA256 hash (for verification)
  - Optional: metadata
"""

def send_file_end(conn, file_hash):
    """Finalize file transfer"""
    payload = bytes.fromhex(file_hash)
    frame = conn.build_frame(frame_type=0x32, payload=payload)
    conn.write_with_ack(frame, timeout=2.0)
    return True

send_file_end(conn, file_hash)
print("✓ File transfer completed and verified")
```

---

## Workflow 5: Complete Script (All Steps Combined)

```python
#!/usr/bin/env python3
"""
Complete end-to-end workflow:
1. HELLO
2. AUTH
3. Export profile
4. Import profile
5. Send file
"""

import sys
from tools.comm_helper import SerialConnection

def main():
    # Configuration
    PORT = "/dev/ttyUSB0"
    TOKEN = "test_token"
    PROFILE_TYPE = 0x02  # voltage
    FILE_TO_SEND = "config.bin"
    
    # Connect
    conn = SerialConnection(port=PORT, baudrate=9600)
    print(f"Connected to {PORT}")
    
    # Step 1: HELLO
    hello = conn.send_hello()
    print(f"✓ Device HELLO: v{hello['version']}")
    
    # Step 2: AUTH
    auth = conn.send_auth(TOKEN)
    if not auth['ack']:
        print("✗ Authentication failed")
        return 1
    print("✓ Authenticated")
    
    # Step 3: Export profile
    profile_export_resp = conn.send_frame(0x10, bytes([PROFILE_TYPE]))
    print(f"✓ Profile export: {len(profile_export_resp)} bytes")
    
    with open("saved_profile.bin", "wb") as f:
        f.write(profile_export_resp)
    
    # Step 4: Import profile
    with open("saved_profile.bin", "rb") as f:
        profile_data = f.read()
    
    conn.send_frame_with_ack(0x11, bytes([PROFILE_TYPE]) + profile_data)
    print("✓ Profile imported")
    
    # Step 5: Send file
    with open(FILE_TO_SEND, "rb") as f:
        file_data = f.read()
    
    import hashlib
    file_hash = hashlib.sha256(file_data).hexdigest()
    
    # Start transfer
    start_payload = len(file_data).to_bytes(2, 'big') + bytes([0x01]) + bytes.fromhex(file_hash)
    conn.send_frame_with_ack(0x30, start_payload)
    print(f"✓ File transfer started: {len(file_data)} bytes")
    
    # Send chunks
    CHUNK_SIZE = 512
    num_chunks = (len(file_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
    for i in range(num_chunks):
        start = i * CHUNK_SIZE
        end = min(start + CHUNK_SIZE, len(file_data))
        chunk = file_data[start:end]
        payload = i.to_bytes(2, 'big') + chunk
        conn.send_frame_with_ack(0x31, payload, retries=3)
        print(f"  Chunk {i+1}/{num_chunks}")
    
    # End transfer
    conn.send_frame_with_ack(0x32, bytes.fromhex(file_hash))
    print("✓ File transfer complete")
    
    print("\n✓ ALL WORKFLOWS COMPLETE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## Testing Each Workflow

### Test Workflow 1: Setup & Auth
```bash
python -c "
from tools.comm_helper import SerialConnection
conn = SerialConnection(port='COM3')
hello = conn.send_hello()
print(f'HELLO: {hello}')
auth = conn.send_auth('test_token')
print(f'AUTH: {auth}')
"
```

### Test Workflow 2: Profile Export
```bash
python -c "
from tools.comm_helper import SerialConnection
conn = SerialConnection(port='COM3')
conn.send_hello()
conn.send_auth('test_token')
# Implement send_frame for profile export (0x10)
"
```

### Test Workflow 3: File Transfer
```bash
python tools/file_transfer.py --serial COM3 --send config.bin --token test_token
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Check port is correct and device is powered |
| "AUTH NACK" | Verify token matches firmware setting |
| "Frame timeout on chunk 3" | Increase `--retry` or reduce `--chunk-size` |
| "CRC mismatch" | Check cable quality; re-flash firmware |

---

## Summary

This guide demonstrated:

✅ **Authentication:** Secure device access via token  
✅ **Profile Management:** Export/import measurement settings  
✅ **File Transfer:** Reliable chunked file upload with verification  

For protocol details, see [PROTOCOL.md](PROTOCOL.md).  
For testing procedures, see [FILE_TRANSFER_TESTING.md](FILE_TRANSFER_TESTING.md).  
For security hardening, see [SECURITY_AND_OTA.md](SECURITY_AND_OTA.md).
