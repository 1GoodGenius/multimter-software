from pc_software.desktop.multimeter import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.multimeter", run_name="__main__")


class MeasurementMode(Enum):
    DC_VOLTAGE = "DC Voltage"
    AC_VOLTAGE = "AC Voltage"
    DC_CURRENT = "DC Current"
    AC_CURRENT = "AC Current"
    RESISTANCE = "Resistance"
    CAPACITANCE = "Capacitance"
    CONTINUITY = "Continuity"
    DIODE = "Diode Test"
    FREQUENCY = "Frequency"
    TEMPERATURE = "Temperature"

class MultimeterSimulator:
    def __init__(self):
        self.mode = MeasurementMode.DC_VOLTAGE
        self.range = "auto"
        self.measurement_history = []
        self.is_connected = True
        
        # Reference values for simulation (stable values)
        self.reference_values = {
            MeasurementMode.DC_VOLTAGE: 12.5,
            MeasurementMode.AC_VOLTAGE: 120.0,
            MeasurementMode.DC_CURRENT: 0.150,
            MeasurementMode.AC_CURRENT: 0.200,
            MeasurementMode.RESISTANCE: 1000.0,
            MeasurementMode.CAPACITANCE: 100.0e-6,
            MeasurementMode.CONTINUITY: 0.05,
            MeasurementMode.DIODE: 0.7,
            MeasurementMode.FREQUENCY: 50.0,
            MeasurementMode.TEMPERATURE: 25.0
        }
        
        # Reduced noise levels for stable readings
        self.noise_levels = {
            MeasurementMode.DC_VOLTAGE: 0.002,  # Reduced from 0.01
            MeasurementMode.AC_VOLTAGE: 0.05,   # Reduced from 0.1
            MeasurementMode.DC_CURRENT: 0.0002, # Reduced from 0.001
            MeasurementMode.AC_CURRENT: 0.0005, # Reduced from 0.002
            MeasurementMode.RESISTANCE: 0.5,   # Reduced from 1.0
            MeasurementMode.CAPACITANCE: 0.1e-6, # Reduced from 0.5e-6
            MeasurementMode.CONTINUITY: 0.005, # Reduced from 0.01
            MeasurementMode.DIODE: 0.005,      # Reduced from 0.01
            MeasurementMode.FREQUENCY: 0.02,   # Reduced from 0.1
            MeasurementMode.TEMPERATURE: 0.05  # Reduced from 0.1
        }
        
        # Drift parameters (slower drift)
        self.drift_rate = 0.0001  # Reduced from 0.001
        self.drift_value = 0.0
        
        # Filtering parameters
        self.filter_buffer = []
        self.filter_size = 5  # Average of last 5 readings
        self.last_stable_value = None
        self.stability_threshold = 0.01  # Threshold for considering value stable
        
    def set_mode(self, mode):
        """Set the measurement mode"""
        if isinstance(mode, str):
            mode = MeasurementMode(mode)
        self.mode = mode
        self.drift_value = 0.0
        self.filter_buffer.clear()  # Clear filter when changing modes
        self.last_stable_value = None
        
    def get_measurement(self):
        """Get a simulated measurement with noise and drift"""
        if not self.is_connected:
            return None, "OL"
            
        base_value = self.reference_values[self.mode]
        noise_level = self.noise_levels[self.mode]
        
        # Generate reading with small noise only
        noise = np.random.normal(0, noise_level)
        
        # Add very slow drift
        self.drift_value += np.random.normal(0, self.drift_rate * base_value)
        self.drift_value *= 0.995  # Even slower return to zero
        
        # Combine for raw measurement
        raw_value = base_value + noise + self.drift_value
        
        # Apply moving average filter for stability
        self.filter_buffer.append(raw_value)
        if len(self.filter_buffer) > self.filter_size:
            self.filter_buffer.pop(0)
        
        # Calculate filtered value
        if len(self.filter_buffer) >= self.filter_size:
            filtered_value = np.mean(self.filter_buffer)
        else:
            filtered_value = raw_value
            
        # Only update stable value if change is significant
        if (self.last_stable_value is None or 
            abs(filtered_value - self.last_stable_value) > self.stability_threshold):
            self.last_stable_value = filtered_value
        
        measured_value = self.last_stable_value if self.last_stable_value is not None else filtered_value
        
        # Apply range limiting
        if self.range != "auto":
            max_value = float(self.range)
            if measured_value > max_value:
                return measured_value, "OL"
                
        # Store in history
        self.measurement_history.append(measured_value)
        if len(self.measurement_history) > 100:
            self.measurement_history.pop(0)
            
        return measured_value, None
        
    def format_display(self, value, error=None):
        """Format the measurement value for display"""
        if error == "OL":
            return "OL"
            
        if value is None:
            return "---"
            
        # Format based on mode and range
        if self.mode == MeasurementMode.DC_VOLTAGE:
            if abs(value) >= 1000:
                return f"{value/1000:.3f} kV"
            elif abs(value) >= 1:
                return f"{value:.3f} V"
            elif abs(value) >= 0.001:
                return f"{value*1000:.1f} mV"
            else:
                return f"{value*1000000:.0f} µV"
                
        elif self.mode == MeasurementMode.AC_VOLTAGE:
            return f"{value:.2f} V"
            
        elif self.mode == MeasurementMode.DC_CURRENT:
            if abs(value) >= 1:
                return f"{value:.3f} A"
            elif abs(value) >= 0.001:
                return f"{value*1000:.1f} mA"
            else:
                return f"{value*1000000:.0f} µA"
                
        elif self.mode == MeasurementMode.AC_CURRENT:
            return f"{value:.3f} A"
            
        elif self.mode == MeasurementMode.RESISTANCE:
            if abs(value) >= 1000000:
                return f"{value/1000000:.2f} MΩ"
            elif abs(value) >= 1000:
                return f"{value/1000:.1f} kΩ"
            elif abs(value) >= 1:
                return f"{value:.1f} Ω"
            else:
                return f"{value*1000:.0f} mΩ"
                
        elif self.mode == MeasurementMode.CAPACITANCE:
            if abs(value) >= 1e-3:
                return f"{value*1000:.2f} mF"
            elif abs(value) >= 1e-6:
                return f"{value*1e6:.1f} µF"
            else:
                return f"{value*1e9:.0f} nF"
                
        elif self.mode == MeasurementMode.CONTINUITY:
            if value < 50:
                return f"{value:.1f} Ω"
            else:
                return "OL"
                
        elif self.mode == MeasurementMode.DIODE:
            return f"{value:.3f} V"
            
        elif self.mode == MeasurementMode.FREQUENCY:
            if abs(value) >= 1000:
                return f"{value/1000:.2f} kHz"
            else:
                return f"{value:.1f} Hz"
                
        elif self.mode == MeasurementMode.TEMPERATURE:
            return f"{value:.1f} °C"
            
        return f"{value:.3f}"
        
    def get_range_info(self):
        """Get current range information"""
        if self.range == "auto":
            return "Auto"
        else:
            return f"{self.range}"