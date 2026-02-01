from pc_software.desktop.diagnostics import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.diagnostics", run_name="__main__")

class SystemDiagnostics:
    def __init__(self):
        self.system_info = self._get_system_info()
        self.dependency_status = self._check_dependencies()
        self.hardware_status = self._check_hardware()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        try:
            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation(),
                "hostname": platform.node()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check if required dependencies are available"""
        dependencies = {
            "tkinter": {"required": True, "optional": False},
            "numpy": {"required": True, "optional": False},
            "matplotlib": {"required": True, "optional": False},
            "pyserial": {"required": True, "optional": False},
            "scipy": {"required": True, "optional": True},  # Optional for advanced features
            "pandas": {"required": False, "optional": True},  # Optional for data analysis
            "pillow": {"required": False, "optional": True},  # Optional for image handling
        }
        
        status = {}
        for dep_name, info in dependencies.items():
            try:
                if dep_name == "tkinter":
                    import tkinter
                    available = True
                    version = tkinter.TkVersion
                elif dep_name == "numpy":
                    import numpy
                    available = True
                    version = numpy.__version__
                elif dep_name == "matplotlib":
                    import matplotlib
                    available = True
                    version = matplotlib.__version__
                elif dep_name == "pyserial":
                    import serial
                    available = True
                    version = serial.__version__
                elif dep_name == "scipy":
                    import scipy
                    available = True
                    version = scipy.__version__
                elif dep_name == "pandas":
                    import pandas
                    available = True
                    version = pandas.__version__
                elif dep_name == "pillow":
                    import PIL
                    available = True
                    version = PIL.__version__
                else:
                    available = False
                    version = None
                
                status[dep_name] = {
                    "available": available,
                    "version": version,
                    "required": info["required"],
                    "optional": info["optional"],
                    "status": "OK" if available else "MISSING"
                }
                
            except ImportError:
                status[dep_name] = {
                    "available": False,
                    "version": None,
                    "required": info["required"],
                    "optional": info["optional"],
                    "status": "MISSING"
                }
        
        return status
    
    def _check_hardware(self) -> Dict[str, Any]:
        """Check hardware availability"""
        hardware_status = {
            "serial_ports": [],
            "bluetooth_available": False,
            "usb_devices": []
        }
        
        try:
            # Check available serial ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                hardware_status["serial_ports"].append({
                    "device": port.device,
                    "name": port.name,
                    "description": port.description,
                    "manufacturer": getattr(port, 'manufacturer', 'Unknown'),
                    "vid": getattr(port, 'vid', None),
                    "pid": getattr(port, 'pid', None)
                })
            
            # Check Bluetooth availability
            system = platform.system()
            if system == "Linux":
                try:
                    result = subprocess.run(["hciconfig"], capture_output=True, text=True, timeout=5)
                    hardware_status["bluetooth_available"] = result.returncode == 0 and "hci" in result.stdout
                except:
                    pass
            elif system == "Windows":
                try:
                    result = subprocess.run(
                        ["powershell", "-Command", "Get-PnpDevice -Class Bluetooth | Select-Object -First 1"], 
                        capture_output=True, text=True, timeout=5
                    )
                    hardware_status["bluetooth_available"] = len(result.stdout.strip()) > 0
                except:
                    pass
            elif system == "Darwin":
                try:
                    result = subprocess.run(["system_profiler", "SPBluetoothDataType"], capture_output=True, text=True, timeout=5)
                    hardware_status["bluetooth_available"] = "Bluetooth" in result.stdout
                except:
                    pass
            
            # Check USB devices (Linux only)
            if system == "Linux":
                try:
                    result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                hardware_status["usb_devices"].append(line.strip())
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error checking hardware: {e}")
        
        return hardware_status
    
    def run_connectivity_tests(self) -> Dict[str, Any]:
        """Run basic connectivity tests"""
        test_results = {
            "serial_test": {"status": "NOT_RUN", "message": ""},
            "bluetooth_test": {"status": "NOT_RUN", "message": ""},
            "file_access_test": {"status": "NOT_RUN", "message": ""},
            "memory_test": {"status": "NOT_RUN", "message": ""}
        }
        
        # Test file access
        try:
            test_file = "test_diagnostics.tmp"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            test_results["file_access_test"]["status"] = "PASS"
            test_results["file_access_test"]["message"] = "File read/write successful"
        except Exception as e:
            test_results["file_access_test"]["status"] = "FAIL"
            test_results["file_access_test"]["message"] = str(e)
        
        # Test memory allocation
        try:
            import numpy as np
            test_array = np.zeros(1000000)  # 1M floats
            del test_array
            test_results["memory_test"]["status"] = "PASS"
            test_results["memory_test"]["message"] = "Memory allocation successful"
        except Exception as e:
            test_results["memory_test"]["status"] = "FAIL"
            test_results["memory_test"]["message"] = str(e)
        
        # Test serial port access
        try:
            if self.hardware_status["serial_ports"]:
                port = self.hardware_status["serial_ports"][0]["device"]
                ser = serial.Serial(port, timeout=1)
                ser.close()
                test_results["serial_test"]["status"] = "PASS"
                test_results["serial_test"]["message"] = f"Serial port {port} accessible"
            else:
                test_results["serial_test"]["status"] = "SKIP"
                test_results["serial_test"]["message"] = "No serial ports found"
        except Exception as e:
            test_results["serial_test"]["status"] = "FAIL"
            test_results["serial_test"]["message"] = str(e)
        
        return test_results
    
    def check_permissions(self) -> Dict[str, Any]:
        """Check file and system permissions"""
        permissions = {
            "config_directory": False,
            "log_directory": False,
            "serial_access": False,
            "bluetooth_access": False
        }
        
        try:
            # Check config directory access
            config_dir = "config"
            os.makedirs(config_dir, exist_ok=True)
            test_file = os.path.join(config_dir, "test_permissions.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            permissions["config_directory"] = True
        except:
            pass
        
        try:
            # Check log directory access
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            test_file = os.path.join(log_dir, "test_permissions.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            permissions["log_directory"] = True
        except:
            pass
        
        # Hardware access permissions would need to be tested during actual connection attempts
        permissions["serial_access"] = len(self.hardware_status["serial_ports"]) > 0
        permissions["bluetooth_access"] = self.hardware_status["bluetooth_available"]
        
        return permissions
    
    def generate_report(self) -> str:
        """Generate a comprehensive diagnostics report"""
        report_lines = []
        report_lines.append("=" * 50)
        report_lines.append("SYSTEM DIAGNOSTICS REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 50)
        
        # System Information
        report_lines.append("\nSYSTEM INFORMATION:")
        for key, value in self.system_info.items():
            report_lines.append(f"  {key}: {value}")
        
        # Dependencies
        report_lines.append("\nDEPENDENCY STATUS:")
        for dep_name, status in self.dependency_status.items():
            required_marker = " [REQUIRED]" if status["required"] else " [OPTIONAL]"
            version_info = f" v{status['version']}" if status["version"] else ""
            report_lines.append(f"  {dep_name}: {status['status']}{version_info}{required_marker}")
        
        # Hardware
        report_lines.append("\nHARDWARE STATUS:")
        report_lines.append(f"  Serial Ports: {len(self.hardware_status['serial_ports'])} found")
        for port in self.hardware_status["serial_ports"]:
            report_lines.append(f"    - {port['device']}: {port['description']}")
        report_lines.append(f"  Bluetooth: {'Available' if self.hardware_status['bluetooth_available'] else 'Not Available'}")
        
        # Connectivity Tests
        tests = self.run_connectivity_tests()
        report_lines.append("\nCONNECTIVITY TESTS:")
        for test_name, result in tests.items():
            status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "○"
            report_lines.append(f"  {status_symbol} {test_name}: {result['message']}")
        
        # Permissions
        permissions = self.check_permissions()
        report_lines.append("\nPERMISSIONS:")
        for perm_name, status in permissions.items():
            status_symbol = "✓" if status else "✗"
            report_lines.append(f"  {status_symbol} {perm_name.replace('_', ' ').title()}")
        
        # Overall Status
        report_lines.append("\nOVERALL STATUS:")
        
        # Check critical dependencies
        missing_critical = any(
            not status["available"] and status["required"] 
            for status in self.dependency_status.values()
        )
        
        # Check hardware access
        hardware_ok = len(self.hardware_status["serial_ports"]) > 0
        
        # Check file permissions
        files_ok = permissions["config_directory"] and permissions["log_directory"]
        
        if missing_critical:
            overall_status = "CRITICAL - Missing required dependencies"
        elif not hardware_ok:
            overall_status = "WARNING - No compatible hardware found"
        elif not files_ok:
            overall_status = "WARNING - File permission issues detected"
        else:
            overall_status = "OK - System ready for use"
        
        report_lines.append(f"  {overall_status}")
        
        return "\n".join(report_lines)
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save diagnostics report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnostics_report_{timestamp}.txt"
        
        try:
            report = self.generate_report()
            with open(filename, 'w') as f:
                f.write(report)
            
            logger.info(f"Diagnostics report saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving diagnostics report: {e}")
            return ""
    
    def get_quick_status(self) -> Dict[str, Any]:
        """Get quick status summary"""
        return {
            "system_ok": True,  # Basic check if Python is running
            "dependencies_ok": all(
                status["available"] for status in self.dependency_status.values() 
                if status["required"]
            ),
            "hardware_available": len(self.hardware_status["serial_ports"]) > 0,
            "bluetooth_available": self.hardware_status["bluetooth_available"],
            "missing_critical_deps": [
                name for name, status in self.dependency_status.items()
                if not status["available"] and status["required"]
            ]
        }