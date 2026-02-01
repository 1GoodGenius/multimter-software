from pc_software.desktop.multimeter_controller import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.multimeter_controller", run_name="__main__")


class MultimeterController:
    def __init__(self, port='COM3', baudrate=9600):
        """Initialize multimeter controller"""
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self.measurement_history = []
        self.max_history = 1000
        
    def connect(self):
        """Connect to Arduino via serial"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2
            )
            time.sleep(2)  # Wait for Arduino to reset
            self.is_connected = True
            print(f"Connected to multimeter on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("Disconnected from multimeter")
    
    def send_command(self, command):
        """Send command to Arduino and read response"""
        if not self.is_connected:
            return None
        
        try:
            self.serial_conn.write((command + '\n').encode())
            response = self.serial_conn.readline().decode().strip()
            return response
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
    
    def measure_voltage(self, range_setting='auto'):
        """Measure voltage"""
        command = f"MEASURE:VOLTAGE:{range_setting.upper()}"
        response = self.send_command(command)
        
        if response:
            try:
                data = json.loads(response)
                measurement = {
                    'timestamp': datetime.now(),
                    'type': 'voltage',
                    'value': data['value'],
                    'unit': data['unit'],
                    'range': data.get('range', 'auto')
                }
                self._add_to_history(measurement)
                return measurement
            except json.JSONDecodeError:
                print(f"Invalid response: {response}")
        
        return None
    
    def measure_current(self, range_setting='auto'):
        """Measure current"""
        command = f"MEASURE:CURRENT:{range_setting.upper()}"
        response = self.send_command(command)
        
        if response:
            try:
                data = json.loads(response)
                measurement = {
                    'timestamp': datetime.now(),
                    'type': 'current',
                    'value': data['value'],
                    'unit': data['unit'],
                    'range': data.get('range', 'auto')
                }
                self._add_to_history(measurement)
                return measurement
            except json.JSONDecodeError:
                print(f"Invalid response: {response}")
        
        return None
    
    def measure_resistance(self, range_setting='auto'):
        """Measure resistance"""
        command = f"MEASURE:RESISTANCE:{range_setting.upper()}"
        response = self.send_command(command)
        
        if response:
            try:
                data = json.loads(response)
                measurement = {
                    'timestamp': datetime.now(),
                    'type': 'resistance',
                    'value': data['value'],
                    'unit': data['unit'],
                    'range': data.get('range', 'auto')
                }
                self._add_to_history(measurement)
                return measurement
            except json.JSONDecodeError:
                print(f"Invalid response: {response}")
        
        return None
    
    def measure_continuity(self):
        """Test continuity"""
        command = "MEASURE:CONTINUITY"
        response = self.send_command(command)
        
        if response:
            try:
                data = json.loads(response)
                measurement = {
                    'timestamp': datetime.now(),
                    'type': 'continuity',
                    'value': data['value'],
                    'unit': data.get('unit', ''),
                    'beep': data.get('beep', False)
                }
                self._add_to_history(measurement)
                return measurement
            except json.JSONDecodeError:
                print(f"Invalid response: {response}")
        
        return None
    
    def set_mode(self, mode):
        """Set measurement mode"""
        valid_modes = ['VOLTAGE_DC', 'VOLTAGE_AC', 'CURRENT_DC', 'CURRENT_AC', 'RESISTANCE', 'CONTINUITY']
        if mode.upper() in valid_modes:
            command = f"SET_MODE:{mode.upper()}"
            return self.send_command(command)
        else:
            print(f"Invalid mode. Valid modes: {valid_modes}")
            return None
    
    def get_status(self):
        """Get device status"""
        response = self.send_command("STATUS")
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                print(f"Invalid response: {response}")
        return None
    
    def _add_to_history(self, measurement):
        """Add measurement to history"""
        self.measurement_history.append(measurement)
        if len(self.measurement_history) > self.max_history:
            self.measurement_history.pop(0)
    
    def continuous_monitor(self, measurement_type='voltage', interval=1.0):
        """Continuously monitor measurements"""
        def monitor():
            while self.is_connected:
                if measurement_type == 'voltage':
                    result = self.measure_voltage()
                elif measurement_type == 'current':
                    result = self.measure_current()
                elif measurement_type == 'resistance':
                    result = self.measure_resistance()
                elif measurement_type == 'continuity':
                    result = self.measure_continuity()
                else:
                    print(f"Unknown measurement type: {measurement_type}")
                    break
                
                if result:
                    print(f"{result['type'].title()}: {result['value']} {result['unit']}")
                
                time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def plot_history(self, measurement_type=None):
        """Plot measurement history"""
        if not self.measurement_history:
            print("No measurements to plot")
            return
        
        # Filter by type if specified
        if measurement_type:
            data = [m for m in self.measurement_history if m['type'] == measurement_type]
        else:
            data = self.measurement_history
        
        if not data:
            print(f"No {measurement_type} measurements to plot")
            return
        
        # Extract timestamps and values
        timestamps = [m['timestamp'] for m in data]
        values = [m['value'] for m in data]
        units = data[0]['unit'] if data else ''
        
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, values, marker='o', linestyle='-')
        plt.title(f"{measurement_type.title() if measurement_type else 'Measurements'} vs Time")
        plt.xlabel('Time')
        plt.ylabel(f"Value ({units})")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    def export_data(self, filename='multimeter_data.csv'):
        """Export measurement history to CSV"""
        if not self.measurement_history:
            print("No data to export")
            return
        
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'type', 'value', 'unit', 'range', 'beep']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for measurement in self.measurement_history:
                row = {
                    'timestamp': measurement['timestamp'],
                    'type': measurement['type'],
                    'value': measurement['value'],
                    'unit': measurement['unit'],
                    'range': measurement.get('range', ''),
                    'beep': measurement.get('beep', '')
                }
                writer.writerow(row)
        
        print(f"Data exported to {filename}")

def main():
    """Example usage"""
    multimeter = MultimeterController()
    
    if multimeter.connect():
        try:
            # Example measurements
            print("Measuring voltage...")
            voltage = multimeter.measure_voltage()
            if voltage:
                print(f"Voltage: {voltage['value']} {voltage['unit']}")
            
            print("Measuring current...")
            current = multimeter.measure_current()
            if current:
                print(f"Current: {current['value']} {current['unit']}")
            
            print("Measuring resistance...")
            resistance = multimeter.measure_resistance()
            if resistance:
                print(f"Resistance: {resistance['value']} {resistance['unit']}")
            
            # Continuous monitoring for 10 seconds
            print("Starting continuous voltage monitoring...")
            monitor_thread = multimeter.continuous_monitor('voltage', 0.5)
            time.sleep(10)
            
            # Export data
            multimeter.export_data()
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        finally:
            multimeter.disconnect()
    else:
        print("Failed to connect to multimeter")

if __name__ == "__main__":
    main()