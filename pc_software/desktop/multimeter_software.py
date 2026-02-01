"""
Arduino Multimeter Software
Professional multimeter application with GUI for measuring voltage, current, and resistance
using Arduino analog pins
Author: Assistant
Date: 2025-06-17
"""

import sys
import serial
import serial.tools.list_ports
import threading
import time
import numpy as np
import socket
import json
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                           QComboBox, QLCDNumber, QFrame, QGroupBox, QMessageBox,
                           QProgressBar, QStatusBar, QMenuBar, QMenu, QAction,
                           QTabWidget, QTextEdit, QSplitter, QDialog, QLineEdit,
                           QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject, pyqtSlot, QSettings
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap

class DataCollector(QObject):
    """Thread-safe data collection from Arduino"""
    data_received = pyqtSignal(float, float, float, float)  # voltage, current, resistance, temperature
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.is_running = False
        self.calibration_voltage = 5.0  # Arduino reference voltage
        self.calibration_offset = 0.0
        
    def connect_arduino(self, port, baudrate=9600):
        """Connect to Arduino"""
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        self.is_running = False
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
    
    def start_reading(self):
        """Start continuous data reading"""
        if self.serial_port and not self.is_running:
            self.is_running = True
            thread = threading.Thread(target=self._read_loop, daemon=True)
            thread.start()
    
    def stop_reading(self):
        """Stop data reading"""
        self.is_running = False
    
    def _read_loop(self):
        """Main reading loop"""
        while self.is_running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line:
                        # Parse data format: "V:1.23,I:0.45,R:1000.0,T:25.5"
                        data = self._parse_data(line)
                        if data:
                            self.data_received.emit(*data)
                time.sleep(0.1)
            except Exception as e:
                print(f"Reading error: {e}")
                break
    
    def _parse_data(self, line):
        """Parse incoming data from Arduino"""
        try:
            parts = line.split(',')
            voltage = float(parts[0].split(':')[1]) if len(parts) > 0 else 0.0
            current = float(parts[1].split(':')[1]) if len(parts) > 1 else 0.0
            resistance = float(parts[2].split(':')[1]) if len(parts) > 2 else 0.0
            temperature = float(parts[3].split(':')[1]) if len(parts) > 3 else 0.0
            return voltage, current, resistance, temperature
        except:
            return None
    
    def calibrate(self, known_voltage):
        """Calibrate with known voltage"""
        self.calibration_voltage = known_voltage
        if self.serial_port:
            self.serial_port.write(f"CAL:{known_voltage}\n".encode())

class MeasurementDisplay(QWidget):
    """Display widget for individual measurements"""
    
    def __init__(self, title, unit, color="blue"):
        super().__init__()
        self.init_ui(title, unit, color)
        self.value = 0.0
        self.history = []
        self.max_history = 100
        
    def init_ui(self, title, unit, color):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # LCD Display
        self.lcd = QLCDNumber(6)
        self.lcd.setSegmentStyle(QLCDNumber.Flat)
        self.lcd.setStyleSheet(f"""
            QLCDNumber {{
                background-color: black;
                color: {color};
                border: 2px solid gray;
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.lcd)
        
        # Unit label
        unit_label = QLabel(unit)
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setFont(QFont("Arial", 10))
        layout.addWidget(unit_label)
        
        self.setLayout(layout)
    
    def update_value(self, value):
        """Update display value"""
        self.value = value
        self.history.append(value)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Format display
        if abs(value) >= 1000:
            self.lcd.display(f"{value:.2e}")
        else:
            self.lcd.display(f"{value:.3f}")

# ... (file continues unchanged) 
# Note: the file content was copied verbatim into the new location for continuity.
