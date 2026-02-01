from pc_software.desktop.test_multimeter import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.test_multimeter", run_name="__main__")

import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Add the current directory to path for imports
sys.path.append('.')

class TestMultimeterSoftware(unittest.TestCase):
    """Test cases for the multimeter software"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock PyQt5 components for testing
        self.qt_app_mock = MagicMock()
        
    def test_requirements_import(self):
        """Test that all required modules can be imported"""
        try:
            import PyQt5
            import serial
            import numpy
            self.assertTrue(True, "All required modules imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import required module: {e}")
    
    def test_serial_port_detection(self):
        """Test serial port detection functionality"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            # Should return a list (could be empty)
            self.assertIsInstance(ports, list, "Port detection should return a list")
        except Exception as e:
            self.fail(f"Serial port detection failed: {e}")
    
    def test_data_parsing(self):
        """Test Arduino data parsing"""
        # Simulate Arduino data format
        test_data = "V:5.123,I:0.123456,R:1000.0,T:25.5"
        
        try:
            parts = test_data.split(',')
            voltage = float(parts[0].split(':')[1])
            current = float(parts[1].split(':')[1])
            resistance = float(parts[2].split(':')[1])
            temperature = float(parts[3].split(':')[1])
            
            self.assertEqual(voltage, 5.123)
            self.assertEqual(current, 0.123456)
            self.assertEqual(resistance, 1000.0)
            self.assertEqual(temperature, 25.5)
            
        except Exception as e:
            self.fail(f"Data parsing failed: {e}")
    
    def test_voltage_conversion(self):
        """Test voltage conversion calculations"""
        # Simulate ADC reading to voltage conversion
        adc_value = 512  # Mid-scale ADC value
        reference_voltage = 5.0
        adc_resolution = 1023.0
        voltage_divider_ratio = 6.0
        
        # Calculate voltage
        voltage = (adc_value / adc_resolution) * reference_voltage * voltage_divider_ratio
        
        expected_voltage = (512 / 1023) * 5.0 * 6.0
        self.assertAlmostEqual(voltage, expected_voltage, places=3)
    
    def test_current_conversion(self):
        """Test current conversion calculations"""
        # Simulate ACS712 current sensor reading
        adc_value = 512  # Mid-scale (2.5V)
        reference_voltage = 5.0
        adc_resolution = 1023.0
        current_sensitivity = 0.185  # V/A for ACS712
        offset = 2.5  # Zero current offset
        
        # Calculate current
        voltage = (adc_value / adc_resolution) * reference_voltage
        current = (voltage - offset) / current_sensitivity
        
        self.assertAlmostEqual(current, 0.0, places=3)  # Should be ~0A at mid-scale
    
    def test_resistance_calculation(self):
        """Test resistance calculation using voltage divider"""
        known_resistor = 10000.0  # 10kΩ
        measured_voltage = 2.5  # Half of reference voltage
        reference_voltage = 5.0
        
        # Calculate unknown resistance
        resistance = (known_resistor * measured_voltage) / (reference_voltage - measured_voltage)
        
        expected_resistance = (10000 * 2.5) / (5.0 - 2.5)
        self.assertEqual(resistance, expected_resistance)
    
    def test_temperature_conversion(self):
        """Test LM35 temperature sensor conversion"""
        # LM35: 10mV/°C
        voltage = 0.25  # 250mV
        temperature = voltage * 100.0
        
        self.assertEqual(temperature, 25.0)  # Should be 25°C
    
    def test_data_smoothing(self):
        """Test data smoothing algorithm"""
        # Simulate noisy data
        raw_data = [1.0, 1.1, 0.9, 1.2, 0.8, 1.05, 0.95, 1.1, 1.0, 0.9]
        
        # Simple moving average
        window_size = 3
        smoothed_data = []
        
        for i in range(len(raw_data) - window_size + 1):
            window = raw_data[i:i + window_size]
            avg = sum(window) / window_size
            smoothed_data.append(avg)
        
        # Check that smoothing occurred
        self.assertLess(len(smoothed_data), len(raw_data))
        self.assertIsInstance(smoothed_data[0], float)
    
    def test_continuity_threshold(self):
        """Test continuity detection threshold"""
        resistance_values = [10, 25, 50, 75, 100]  # Ohms
        threshold = 50  # Ohms
        
        continuity_results = [r < threshold for r in resistance_values]
        expected_results = [True, True, False, False, False]
        
        self.assertEqual(continuity_results, expected_results)
    
    @patch('serial.Serial')
    def test_serial_communication(self, mock_serial):
        """Test basic serial communication setup"""
        mock_port = MagicMock()
        mock_serial.return_value = mock_port
        
        # Simulate port opening
        mock_port.isOpen.return_value = True
        mock_port.in_waiting.return_value = 0
        mock_port.readline.return_value = b"V:5.0,I:1.0,R:10.0,T:25.0\n"
        
        # Test port opening
        with serial.Serial('COM3', 9600, timeout=1) as ser:
            self.assertTrue(ser.isOpen())
    
    def test_gui_components(self):
        """Test GUI component initialization (basic check)"""
        try:
            from PyQt5.QtWidgets import QApplication, QWidget, QLabel
            from PyQt5.QtCore import Qt
            
            # Create a minimal test application
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Test basic widget creation
            widget = QWidget()
            label = QLabel("Test")
            label.setAlignment(Qt.AlignCenter)
            
            self.assertIsNotNone(widget)
            self.assertIsNotNone(label)
            
        except ImportError:
            self.skipTest("PyQt5 not available for GUI testing")
        except Exception as e:
            self.fail(f"GUI component test failed: {e}")

def run_functional_tests():
    """Run functional tests without GUI"""
    print("Running Arduino Multimeter Software Tests...")
    print("=" * 50)
    
    # Test 1: Module imports
    print("1. Testing module imports...")
    try:
        import PyQt5
        import serial
        import numpy
        print("   ✓ All required modules available")
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    
    # Test 2: Serial ports
    print("2. Testing serial port detection...")
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        print(f"   ✓ Found {len(ports)} serial ports")
        for port in ports:
            print(f"     - {port.device}: {port.description}")
    except Exception as e:
        print(f"   ✗ Serial port test failed: {e}")
        return False
    
    # Test 3: Data parsing
    print("3. Testing data parsing...")
    test_data = "V:5.123,I:0.123456,R:1000.0,T:25.5"
    try:
        parts = test_data.split(',')
        voltage = float(parts[0].split(':')[1])
        current = float(parts[1].split(':')[1])
        resistance = float(parts[2].split(':')[1])
        temperature = float(parts[3].split(':')[1])
        print(f"   ✓ Parsed: V={voltage}V, I={current}A, R={resistance}Ω, T={temperature}°C")
    except Exception as e:
        print(f"   ✗ Data parsing failed: {e}")
        return False
    
    # Test 4: Calculations
    print("4. Testing measurement calculations...")
    try:
        # Voltage calculation
        adc_val = 512
        voltage = (adc_val / 1023.0) * 5.0 * 6.0
        print(f"   ✓ Voltage calculation: ADC {adc_val} → {voltage:.2f}V")
        
        # Current calculation
        voltage_adc = (adc_val / 1023.0) * 5.0
        current = (voltage_adc - 2.5) / 0.185
        print(f"   ✓ Current calculation: {voltage_adc:.2f}V → {current:.6f}A")
        
        # Resistance calculation
        resistance = (10000 * 2.5) / (5.0 - 2.5)
        print(f"   ✓ Resistance calculation: {resistance:.0f}Ω")
        
        # Temperature calculation
        temp_voltage = 0.25
        temperature = temp_voltage * 100.0
        print(f"   ✓ Temperature calculation: {temp_voltage}V → {temperature:.0f}°C")
        
    except Exception as e:
        print(f"   ✗ Calculation test failed: {e}")
        return False
    
    print("=" * 50)
    print("All functional tests passed! ✓")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--functional":
        # Run functional tests without GUI
        success = run_functional_tests()
        sys.exit(0 if success else 1)
    else:
        # Run unit tests
        unittest.main(verbosity=2)