import logging
import platform
import subprocess
import random
import time
from typing import Optional, List, Dict, Any
from ..floating_input_detector import MultimeterReadingProcessor, ReadingStatus

logger = logging.getLogger(__name__)

class BluetoothManager:
    def __init__(self):
        self.is_connected = False
        self.connected_device = None
        self.adapter_available = self.check_adapter_availability()
        self.reading_processor = MultimeterReadingProcessor()
        self.floating_simulation_enabled = False
    
    def check_adapter_availability(self) -> bool:
        """Check if Bluetooth adapter is available"""
        try:
            system = platform.system()
            if system == "Linux":
                result = subprocess.run(["hciconfig"], capture_output=True, text=True)
                return "hci0" in result.stdout or "hci" in result.stdout
            elif system == "Windows":
                result = subprocess.run(["powershell", "-Command", "Get-PnpDevice -Class Bluetooth -FriendlyName '*Bluetooth*' | Select-Object -First 1"], capture_output=True, text=True)
                return len(result.stdout.strip()) > 0
            elif system == "Darwin":
                result = subprocess.run(["system_profiler", "SPBluetoothDataType"], capture_output=True, text=True)
                return "Bluetooth" in result.stdout
            return False
        except Exception as e:
            logger.error(f"Error checking Bluetooth adapter: {e}")
            return False
    
    def scan_devices(self) -> List[Dict[str, Any]]:
        """Scan for available Bluetooth devices"""
        devices = []
        try:
            # Simulated device scan for demo purposes
            devices = [
                {"name": "BT-DMM-001", "address": "00:1A:7D:DA:71:13", "rssi": -65},
                {"name": "BT-DMM-002", "address": "00:1A:7D:DA:71:14", "rssi": -78},
                {"name": "BT-DMM-003", "address": "00:1A:7D:DA:71:15", "rssi": -82},
            ]
        except Exception as e:
            logger.error(f"Error scanning devices: {e}")
        return devices
    
    def connect(self, device_address: str) -> bool:
        """Connect to a Bluetooth device"""
        try:
            # Simulated connection
            self.is_connected = True
            self.connected_device = device_address
            logger.info(f"Connected to device: {device_address}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to device {device_address}: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from current device"""
        try:
            self.is_connected = False
            self.connected_device = None
            logger.info("Disconnected from device")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def send_command(self, command: str) -> Optional[str]:
        """Send command to connected device"""
        if not self.is_connected:
            return None
        
        try:
            # Generate simulated readings with floating input behavior
            raw_response = self._generate_simulated_response(command)
            
            # Process the reading through the floating input detector
            value, status, display_message = self.reading_processor.process_reading(raw_response)
            
            return {
                "raw": raw_response,
                "value": value,
                "status": status.value,
                "display": display_message,
                "statistics": self.reading_processor.get_current_reading()
            }
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
            
    def _generate_simulated_response(self, command: str) -> str:
        """Generate simulated multimeter response with optional floating input"""
        if self.floating_simulation_enabled:
            # Simulate floating input behavior
            if command == "MEAS:VOLT:DC?":
                # Generate random floating readings
                floating_value = random.uniform(-0.5, 0.5) + random.uniform(-2, 2) * random.random()
                return f"{floating_value:.3f}V"
            elif command == "MEAS:CURR:DC?":
                floating_value = random.uniform(-0.1, 0.1) + random.uniform(-0.5, 0.5) * random.random()
                return f"{floating_value:.4f}A"
            elif command == "MEAS:RES?":
                floating_value = random.uniform(100, 10000) * (1 + random.uniform(-0.5, 0.5))
                return f"{floating_value:.1f}Ω"
        else:
            # Normal stable readings
            if command == "MEAS:VOLT:DC?":
                return "12.34V"
            elif command == "MEAS:CURR:DC?":
                return "1.23A"
            elif command == "MEAS:RES?":
                return "1.23KΩ"
        
        return "OK"
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            "connected": self.is_connected,
            "device": self.connected_device,
            "adapter_available": self.adapter_available,
            "floating_simulation": self.floating_simulation_enabled,
            "reading_processor": self.reading_processor.get_current_reading()
        }
        
    def enable_floating_simulation(self, enabled: bool):
        """Enable or disable floating input simulation for testing"""
        self.floating_simulation_enabled = enabled
        if enabled:
            self.reading_processor.reset_processor()
        logger.info(f"Floating simulation {'enabled' if enabled else 'disabled'}")
        
    def reset_reading_processor(self):
        """Reset the reading processor state"""
        self.reading_processor.reset_processor()
