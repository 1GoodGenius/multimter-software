from pc_software.desktop.settings import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.settings", run_name="__main__")


logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self, config_file: str = "config/settings.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        self.settings: Dict[str, Any] = {}
        self.default_settings = self._get_default_settings()
        self.load_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings"""
        return {
            "device": {
                "baudrate": 115200,
                "timeout": 1.0,
                "auto_reconnect": True,
                "connection_timeout": 5.0
            },
            "bluetooth": {
                "auto_scan": True,
                "scan_timeout": 10.0,
                "preferred_device": None
            },
            "oscilloscope": {
                "sample_rate": 1000,
                "voltage_range": 5.0,
                "time_base": 0.001,
                "trigger_mode": "auto",
                "trigger_level": 1.0,
                "trigger_edge": "rising"
            },
            "measurement": {
                "voltage_range": "AUTO",
                "current_range": "AUTO",
                "resistance_range": "AUTO",
                "measurement_rate": 10,
                "auto_zero": True,
                "averaging": 4
            },
            "signal_processing": {
                "enable_filtering": True,
                "filter_type": "lowpass",
                "filter_cutoff": 100.0,
                "filter_order": 4,
                "enable_windowing": True,
                "window_type": "hann"
            },
            "logging": {
                "auto_log": False,
                "log_interval": 1.0,
                "max_log_size": 100,
                "log_directory": "logs",
                "export_format": "csv"
            },
            "display": {
                "theme": "dark",
                "font_size": 12,
                "show_grid": True,
                "show_measurements": True,
                "auto_scale": True,
                "refresh_rate": 60
            },
            "data_export": {
                "default_format": "csv",
                "include_timestamp": True,
                "decimal_places": 3,
                "separator": ","
            },
            "application": {
                "window_width": 1200,
                "window_height": 800,
                "remember_position": True,
                "check_updates": True,
                "language": "en"
            }
        }
    
    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as file:
                    loaded_settings = json.load(file)
                    # Merge with defaults to handle new settings
                    self.settings = self._merge_settings(self.default_settings, loaded_settings)
                    logger.info(f"Settings loaded from {self.config_file}")
            else:
                # Use default settings if no file exists
                self.settings = self.default_settings.copy()
                self.save_settings()
                logger.info("Using default settings")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.settings = self.default_settings.copy()
            return False
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            with open(self.config_file, 'w') as file:
                json.dump(self.settings, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def _merge_settings(self, defaults: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded settings with defaults"""
        merged = defaults.copy()
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_settings(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value using dot notation (e.g., 'device.baudrate')"""
        try:
            keys = key.split('.')
            value = self.settings
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting setting '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set setting value using dot notation"""
        try:
            keys = key.split('.')
            settings = self.settings
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in settings:
                    settings[k] = {}
                settings = settings[k]
            
            # Set the value
            settings[keys[-1]] = value
            
            logger.info(f"Setting '{key}' updated to '{value}'")
            return True
            
        except Exception as e:
            logger.error(f"Error setting '{key}': {e}")
            return False
    
    def reset_to_defaults(self, category: Optional[str] = None) -> bool:
        """Reset settings to defaults (all or specific category)"""
        try:
            if category:
                if category in self.default_settings:
                    self.settings[category] = self.default_settings[category].copy()
                    logger.info(f"Reset '{category}' settings to defaults")
                else:
                    logger.warning(f"Unknown settings category: {category}")
                    return False
            else:
                self.settings = self.default_settings.copy()
                logger.info("Reset all settings to defaults")
            
            return self.save_settings()
            
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False
    
    def export_settings(self, filepath: str) -> bool:
        """Export current settings to a file"""
        try:
            export_path = Path(filepath)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w') as file:
                json.dump(self.settings, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, filepath: str, merge: bool = True) -> bool:
        """Import settings from a file"""
        try:
            import_path = Path(filepath)
            if not import_path.exists():
                logger.error(f"Settings file not found: {filepath}")
                return False
            
            with open(import_path, 'r') as file:
                imported_settings = json.load(file)
            
            if merge:
                self.settings = self._merge_settings(self.settings, imported_settings)
            else:
                self.settings = imported_settings
            
            logger.info(f"Settings imported from {filepath}")
            return self.save_settings()
            
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False
    
    def validate_settings(self) -> Dict[str, Any]:
        """Validate current settings and return any issues"""
        issues = []
        warnings = []
        
        try:
            # Validate device settings
            baudrate = self.get("device.baudrate")
            if not isinstance(baudrate, int) or baudrate <= 0:
                issues.append("device.baudrate must be a positive integer")
            
            timeout = self.get("device.timeout")
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                issues.append("device.timeout must be a positive number")
            
            # Validate oscilloscope settings
            sample_rate = self.get("oscilloscope.sample_rate")
            if not isinstance(sample_rate, int) or sample_rate <= 0:
                issues.append("oscilloscope.sample_rate must be a positive integer")
            
            voltage_range = self.get("oscilloscope.voltage_range")
            if not isinstance(voltage_range, (int, float)) or voltage_range <= 0:
                issues.append("oscilloscope.voltage_range must be a positive number")
            
            # Validate display settings
            font_size = self.get("display.font_size")
            if not isinstance(font_size, int) or font_size < 8 or font_size > 24:
                warnings.append("display.font_size should be between 8 and 24")
            
            refresh_rate = self.get("display.refresh_rate")
            if not isinstance(refresh_rate, int) or refresh_rate < 1 or refresh_rate > 120:
                warnings.append("display.refresh_rate should be between 1 and 120 Hz")
            
        except Exception as e:
            issues.append(f"Error during validation: {e}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings"""
        return self.settings.copy()
    
    def get_settings_summary(self) -> str:
        """Get a human-readable summary of current settings"""
        try:
            summary = []
            summary.append("=== Current Settings Summary ===\n")
            
            # Device settings
            summary.append("Device:")
            summary.append(f"  Baudrate: {self.get('device.baudrate')}")
            summary.append(f"  Timeout: {self.get('device.timeout')}s")
            summary.append(f"  Auto-reconnect: {self.get('device.auto_reconnect')}")
            
            # Oscilloscope settings
            summary.append("\nOscilloscope:")
            summary.append(f"  Sample Rate: {self.get('oscilloscope.sample_rate')} Hz")
            summary.append(f"  Voltage Range: ±{self.get('oscilloscope.voltage_range')}V")
            summary.append(f"  Time Base: {self.get('oscilloscope.time_base')}s")
            
            # Display settings
            summary.append("\nDisplay:")
            summary.append(f"  Theme: {self.get('display.theme')}")
            summary.append(f"  Font Size: {self.get('display.font_size')}")
            summary.append(f"  Refresh Rate: {self.get('display.refresh_rate')} Hz")
            
            # Logging settings
            summary.append("\nLogging:")
            summary.append(f"  Auto-log: {self.get('logging.auto_log')}")
            summary.append(f"  Log Directory: {self.get('logging.log_directory')}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Error generating settings summary: {e}")
            return "Error generating settings summary"