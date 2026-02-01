from pc_software.desktop.keithley_2400 import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.keithley_2400", run_name="__main__")


logger = logging.getLogger(__name__)

class MeasurementMode(Enum):
    VOLTAGE_DC = "VOLT:DC"
    VOLTAGE_AC = "VOLT:AC"
    CURRENT_DC = "CURR:DC"
    CURRENT_AC = "CURR:AC"
    RESISTANCE = "RES"
    RESISTANCE_4WIRE = "FRES"
    POWER = "POW"

@dataclass
class Measurement:
    value: float
    unit: str
    timestamp: float
    mode: MeasurementMode
    range: Optional[float] = None
    compliance: Optional[float] = None

class Keithley2400:
    def __init__(self, resource_string: str = "GPIB::24::INSTR"):
        self.resource_string = resource_string
        self.instrument = None
        self.resource_manager = None
        self.is_connected = False
        self.current_mode = MeasurementMode.VOLTAGE_DC
        self.safety_limits = {
            'max_voltage': 210.0,  # 20% safety margin
            'max_current': 1.05,    # 20% safety margin
            'max_power': 20.0       # 20% safety margin
        }
        
    def connect(self) -> bool:
        """Connect to Keithley 2400 instrument"""
        try:
            self.resource_manager = pyvisa.ResourceManager()
            self.instrument = self.resource_manager.open_resource(self.resource_string)
            
            # Configure instrument
            self.instrument.write("*RST")  # Reset
            self.instrument.write("*CLS")  # Clear status
            self.instrument.write("*IDN?")
            idn = self.instrument.read()
            
            logger.info(f"Connected to: {idn.strip()}")
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Keithley 2400: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Safely disconnect from instrument"""
        try:
            if self.instrument:
                self.instrument.write("OUTP:STAT OFF")  # Turn off output
                self.instrument.close()
            if self.resource_manager:
                self.resource_manager.close()
            self.is_connected = False
            logger.info("Disconnected from Keithley 2400")
            return True
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return False
    
    def configure_safety_limits(self, max_voltage: float = None, 
                               max_current: float = None, max_power: float = None):
        """Configure safety limits"""
        if max_voltage:
            self.safety_limits['max_voltage'] = max_voltage
        if max_current:
            self.safety_limits['max_current'] = max_current
        if max_power:
            self.safety_limits['max_power'] = max_power
    
    def set_mode(self, mode: MeasurementMode) -> bool:
        """Set measurement mode"""
        try:
            if mode == MeasurementMode.VOLTAGE_DC:
                self.instrument.write(":SENS:FUNC 'VOLT:DC'")
            elif mode == MeasurementMode.VOLTAGE_AC:
                self.instrument.write(":SENS:FUNC 'VOLT:AC'")
            elif mode == MeasurementMode.CURRENT_DC:
                self.instrument.write(":SENS:FUNC 'CURR:DC'")
            elif mode == MeasurementMode.CURRENT_AC:
                self.instrument.write(":SENS:FUNC 'CURR:AC'")
            elif mode == MeasurementMode.RESISTANCE:
                self.instrument.write(":SENS:FUNC 'RES'")
            elif mode == MeasurementMode.RESISTANCE_4WIRE:
                self.instrument.write(":SENS:FUNC 'FRES'")
            elif mode == MeasurementMode.POWER:
                self.instrument.write(":SENS:FUNC 'POW'")
            
            self.current_mode = mode
            return True
        except Exception as e:
            logger.error(f"Failed to set mode {mode}: {e}")
            return False
    
    def set_range(self, range_value: float) -> bool:
        """Set measurement range"""
        try:
            if self.current_mode in [MeasurementMode.VOLTAGE_DC, MeasurementMode.VOLTAGE_AC]:
                self.instrument.write(f":SENS:VOLT:RANG {range_value}")
            elif self.current_mode in [MeasurementMode.CURRENT_DC, MeasurementMode.CURRENT_AC]:
                self.instrument.write(f":SENS:CURR:RANG {range_value}")
            elif self.current_mode in [MeasurementMode.RESISTANCE, MeasurementMode.RESISTANCE_4WIRE]:
                self.instrument.write(f":SENS:RES:RANG {range_value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set range {range_value}: {e}")
            return False
    
    def measure_single(self, mode: Optional[MeasurementMode] = None) -> Optional[Measurement]:
        """Perform a single measurement"""
        if not self.is_connected:
            logger.error("Not connected to instrument")
            return None
        
        try:
            if mode:
                self.set_mode(mode)
            
            # Send measurement command
            if self.current_mode == MeasurementMode.VOLTAGE_DC:
                self.instrument.write("MEAS:VOLT:DC?")
                response = self.instrument.read().strip()
                value = float(response)
                unit = "V"
            elif self.current_mode == MeasurementMode.CURRENT_DC:
                self.instrument.write("MEAS:CURR:DC?")
                response = self.instrument.read().strip()
                value = float(response)
                unit = "A"
            elif self.current_mode == MeasurementMode.RESISTANCE:
                self.instrument.write("MEAS:RES?")
                response = self.instrument.read().strip()
                value = float(response)
                unit = "Ω"
            elif self.current_mode == MeasurementMode.POWER:
                # Calculate power from voltage and current
                self.instrument.write("MEAS:VOLT:DC?")
                voltage = float(self.instrument.read().strip())
                self.instrument.write("MEAS:CURR:DC?")
                current = float(self.instrument.read().strip())
                value = voltage * current
                unit = "W"
            else:
                logger.error(f"Unsupported measurement mode: {self.current_mode}")
                return None
            
            # Check safety limits
            if not self._check_safety_limits(value, unit):
                logger.warning(f"Measurement {value}{unit} exceeds safety limits")
                return None
            
            measurement = Measurement(
                value=value,
                unit=unit,
                timestamp=time.time(),
                mode=self.current_mode
            )
            
            return measurement
            
        except Exception as e:
            logger.error(f"Measurement failed: {e}")
            return None
    
    def _check_safety_limits(self, value: float, unit: str) -> bool:
        """Check if measurement is within safety limits"""
        if unit == "V" and abs(value) > self.safety_limits['max_voltage']:
            return False
        elif unit == "A" and abs(value) > self.safety_limits['max_current']:
            return False
        elif unit == "W" and abs(value) > self.safety_limits['max_power']:
            return False
        return True
    
    def enable_output(self, enable: bool = True) -> bool:
        """Enable or disable source output"""
        try:
            state = "ON" if enable else "OFF"
            self.instrument.write(f"OUTP:STAT {state}")
            return True
        except Exception as e:
            logger.error(f"Failed to set output state: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get instrument status"""
        try:
            self.instrument.write("*IDN?")
            idn = self.instrument.read().strip()
            self.instrument.write(":OUTP:STAT?")
            output_state = self.instrument.read().strip()
            
            return {
                'connected': self.is_connected,
                'idn': idn,
                'output_state': output_state,
                'current_mode': self.current_mode.value,
                'safety_limits': self.safety_limits
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'connected': False, 'error': str(e)}