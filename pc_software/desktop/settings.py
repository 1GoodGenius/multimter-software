import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

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
            # (rest copied)
        }
