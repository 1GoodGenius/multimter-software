import serial
import time
import json
import matplotlib.pyplot as plt
from datetime import datetime
import threading

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

# ... (file continues unchanged)
