import logging
import numpy as np
import serial
import serial.tools.list_ports
from typing import Optional, List, Dict, Any, Tuple
import time

logger = logging.getLogger(__name__)

class DeviceCommunicator:
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False

# (rest of file copied)
