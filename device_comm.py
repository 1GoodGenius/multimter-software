from pc_software.desktop.device_comm import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.device_comm", run_name="__main__")

class DeviceCommunicator:
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.waveform_buffer: List[float] = []
        self.max_buffer_size = 1000
    
    def list_available_ports(self) -> List[Dict[str, str]]:
        """List all available COM ports"""
        ports = []
        try:
            port_list = serial.tools.list_ports.comports()
            for port in port_list:
                ports.append({
                    "device": port.device,
                    "name": port.name,
                    "description": port.description,
                    "manufacturer": getattr(port, 'manufacturer', 'Unknown')
                })
        except Exception as e:
            logger.error(f"Error listing ports: {e}")
        return ports
    
    def connect(self, port: Optional[str] = None) -> bool:
        """Connect to device via serial"""
        if port:
            self.port = port
        
        if not self.port:
            logger.error("No port specified")
            return False
        
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            time.sleep(0.1)  # Wait for connection to stabilize
            self.is_connected = True
            logger.info(f"Connected to {self.port}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to {self.port}: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from device"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            self.is_connected = False
            logger.info("Disconnected from device")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def send_command(self, command: str) -> bool:
        """Send command to device"""
        if not self.is_connected or not self.serial_connection:
            return False
        
        try:
            command_bytes = command.encode('utf-8') + b'\n'
            self.serial_connection.write(command_bytes)
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False
    
    def read_response(self) -> Optional[str]:
        """Read response from device"""
        if not self.is_connected or not self.serial_connection:
            return None
        
        try:
            response = self.serial_connection.readline().decode('utf-8').strip()
            return response
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            return None
    
    def get_measurement(self) -> Optional[Dict[str, Any]]:
        """Get measurement data from device"""
        if not self.send_command("MEAS?"):
            return None
        
        response = self.read_response()
        if response:
            try:
                # Parse response format: "VOLT:12.34,CURR:1.23,RES:1.23K"
                parts = response.split(',')
                data = {}
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        data[key.lower()] = value
                
                return {
                    "voltage": data.get("volt", "0V"),
                    "current": data.get("curr", "0A"), 
                    "resistance": data.get("res", "0Ω"),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error parsing measurement: {e}")
        
        return None
    
    def capture_waveform(self, duration: float = 1.0, sample_rate: int = 1000) -> Optional[np.ndarray]:
        """Capture waveform data from device"""
        if not self.is_connected:
            return None
        
        try:
            self.send_command(f"WAVECAPT:{duration}:{sample_rate}")
            
            # Clear buffer
            self.waveform_buffer.clear()
            
            # Read waveform data points
            samples = int(duration * sample_rate)
            start_time = time.time()
            
            while len(self.waveform_buffer) < samples and (time.time() - start_time) < duration + 2:
                response = self.read_response()
                if response and response.startswith("DATA:"):
                    try:
                        value = float(response[5:])  # Remove "DATA:" prefix
                        self.waveform_buffer.append(value)
                    except ValueError:
                        continue
            
            if self.waveform_buffer:
                return np.array(self.waveform_buffer)
            else:
                logger.warning("No waveform data captured")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing waveform: {e}")
            return None
    
    def get_device_info(self) -> Optional[Dict[str, str]]:
        """Get device information"""
        if not self.send_command("INFO?"):
            return None
        
        response = self.read_response()
        if response:
            try:
                # Parse response format: "MODEL:SmartScope,V1.0,SERIAL:12345"
                parts = response.split(',')
                info = {}
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        info[key.lower()] = value
                return info
            except Exception as e:
                logger.error(f"Error parsing device info: {e}")
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status"""
        return {
            "connected": self.is_connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "buffer_size": len(self.waveform_buffer)
        }