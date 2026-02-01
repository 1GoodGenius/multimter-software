from pc_software.desktop.multimeter_software import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.multimeter_software", run_name="__main__")

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

class GraphWidget(QWidget):
    """Simple graph widget for displaying measurement history"""
    
    def __init__(self, title, color):
        super().__init__()
        self.title = title
        self.color = color
        self.data = []
        self.max_points = 200
        self.setMinimumHeight(150)
        
    def add_data(self, value):
        """Add new data point"""
        self.data.append(value)
        if len(self.data) > self.max_points:
            self.data.pop(0)
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event for drawing graph"""
        from PyQt5.QtGui import QPainter, QPen
        from PyQt5.QtCore import QPoint
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # Draw grid
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(0, self.width(), 40):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 30):
            painter.drawLine(0, i, self.width(), i)
        
        # Draw data
        if len(self.data) > 1:
            painter.setPen(QPen(QColor(self.color), 2))
            
            # Normalize data
            if max(self.data) != min(self.data):
                normalized = [(x - min(self.data)) / (max(self.data) - min(self.data)) 
                             for x in self.data]
            else:
                normalized = [0.5] * len(self.data)
            
            # Draw lines
            x_step = self.width() / (self.max_points - 1)
            points = []
            for i, value in enumerate(normalized):
                x = i * x_step
                y = self.height() - (value * self.height())
                points.append(QPoint(int(x), int(y)))
            
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i+1])

class MultimeterGUI(QMainWindow):
    """Main GUI application for Arduino Multimeter"""
    
    def __init__(self):
        super().__init__()
        self.data_collector = DataCollector()
        self.init_ui()
        self.setup_connections()
        self.scan_ports()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Arduino Multimeter Software")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Connection group
        conn_group = QGroupBox("Arduino Connection")
        conn_layout = QGridLayout()
        
        self.port_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh Ports")
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)
        
        conn_layout.addWidget(QLabel("Port:"), 0, 0)
        conn_layout.addWidget(self.port_combo, 0, 1, 1, 2)
        conn_layout.addWidget(self.refresh_btn, 1, 0)
        conn_layout.addWidget(self.connect_btn, 1, 1)
        conn_layout.addWidget(self.disconnect_btn, 1, 2)
        
        conn_group.setLayout(conn_layout)
        left_layout.addWidget(conn_group)
        
        # Mode selection
        mode_group = QGroupBox("Measurement Mode")
        mode_layout = QVBoxLayout()
        
        self.voltage_btn = QPushButton("Voltage Mode")
        self.current_btn = QPushButton("Current Mode")
        self.resistance_btn = QPushButton("Resistance Mode")
        self.continuity_btn = QPushButton("Continuity Test")
        
        mode_layout.addWidget(self.voltage_btn)
        mode_layout.addWidget(self.current_btn)
        mode_layout.addWidget(self.resistance_btn)
        mode_layout.addWidget(self.continuity_btn)
        
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        
        # Range selection
        range_group = QGroupBox("Range Selection")
        range_layout = QVBoxLayout()
        
        self.auto_range_btn = QPushButton("Auto Range")
        self.manual_range_combo = QComboBox()
        self.manual_range_combo.addItems(["Manual: 2V", "Manual: 20V", "Manual: 200V"])
        self.manual_range_combo.setEnabled(False)
        
        range_layout.addWidget(self.auto_range_btn)
        range_layout.addWidget(self.manual_range_combo)
        
        range_group.setLayout(range_layout)
        left_layout.addWidget(range_group)
        
        # Calibration
        cal_group = QGroupBox("Calibration")
        cal_layout = QVBoxLayout()
        
        self.calibrate_btn = QPushButton("Calibrate")
        self.zero_btn = QPushButton("Zero Offset")
        
        cal_layout.addWidget(self.calibrate_btn)
        cal_layout.addWidget(self.zero_btn)
        
        cal_group.setLayout(cal_layout)
        left_layout.addWidget(cal_group)
        
        left_layout.addStretch()
        
        # Right panel - Displays
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Main display tab
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout(main_tab)
        
        # Measurement displays
        displays_layout = QGridLayout()
        
        self.voltage_display = MeasurementDisplay("Voltage", "V", "red")
        self.current_display = MeasurementDisplay("Current", "A", "blue")
        self.resistance_display = MeasurementDisplay("Resistance", "Ω", "green")
        self.temperature_display = MeasurementDisplay("Temperature", "°C", "orange")
        
        displays_layout.addWidget(self.voltage_display, 0, 0)
        displays_layout.addWidget(self.current_display, 0, 1)
        displays_layout.addWidget(self.resistance_display, 1, 0)
        displays_layout.addWidget(self.temperature_display, 1, 1)
        
        main_tab_layout.addLayout(displays_layout)
        
        # Status indicators
        status_layout = QHBoxLayout()
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        self.measuring_status = QLabel("Not Measuring")
        self.measuring_status.setStyleSheet("color: gray;")
        
        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.connection_status)
        status_layout.addWidget(self.measuring_status)
        status_layout.addStretch()
        
        main_tab_layout.addLayout(status_layout)
        
        self.tab_widget.addTab(main_tab, "Main Display")
        
        # Graphs tab
        graphs_tab = QWidget()
        graphs_layout = QVBoxLayout(graphs_tab)
        
        self.voltage_graph = GraphWidget("Voltage", "red")
        self.current_graph = GraphWidget("Current", "blue")
        self.resistance_graph = GraphWidget("Resistance", "green")
        
        graphs_layout.addWidget(QLabel("Voltage"))
        graphs_layout.addWidget(self.voltage_graph)
        graphs_layout.addWidget(QLabel("Current"))
        graphs_layout.addWidget(self.current_graph)
        graphs_layout.addWidget(QLabel("Resistance"))
        graphs_layout.addWidget(self.resistance_graph)
        
        self.tab_widget.addTab(graphs_tab, "Graphs")
        
        # Data log tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.clear_log_btn = QPushButton("Clear Log")
        
        log_layout.addWidget(self.log_text)
        log_layout.addWidget(self.clear_log_btn)
        
        self.tab_widget.addTab(log_tab, "Data Log")
        
        right_layout.addWidget(self.tab_widget)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Menu bar
        self.create_menu_bar()
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        export_action = QAction('Export Data', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        website_action = QAction('Visit Website', self)
        website_action.triggered.connect(self.open_website)
        help_menu.addAction(website_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Connection buttons
        self.refresh_btn.clicked.connect(self.scan_ports)
        self.connect_btn.clicked.connect(self.connect_arduino)
        self.disconnect_btn.clicked.connect(self.disconnect_arduino)
        
        # Mode buttons
        self.voltage_btn.clicked.connect(lambda: self.set_mode('voltage'))
        self.current_btn.clicked.connect(lambda: self.set_mode('current'))
        self.resistance_btn.clicked.connect(lambda: self.set_mode('resistance'))
        self.continuity_btn.clicked.connect(self.test_continuity)
        
        # Range buttons
        self.auto_range_btn.clicked.connect(self.set_auto_range)
        
        # Calibration buttons
        self.calibrate_btn.clicked.connect(self.calibrate)
        self.zero_btn.clicked.connect(self.zero_offset)
        
        # Data collector
        self.data_collector.data_received.connect(self.update_measurements)
        
        # Log
        self.clear_log_btn.clicked.connect(self.clear_log)
    
    def scan_ports(self):
        """Scan for available Arduino ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        arduino_ports = []
        for port in ports:
            if 'Arduino' in port.description or 'CH340' in port.description or 'USB' in port.description:
                arduino_ports.append(f"{port.device} - {port.description}")
        
        if arduino_ports:
            self.port_combo.addItems(arduino_ports)
        else:
            self.port_combo.addItem("No Arduino found")
    
    def connect_arduino(self):
        """Connect to selected Arduino"""
        if self.port_combo.currentText() == "No Arduino found":
            QMessageBox.warning(self, "Connection Error", "No Arduino port found!")
            return
        
        port = self.port_combo.currentText().split(' - ')[0]
        
        if self.data_collector.connect_arduino(port):
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.data_collector.start_reading()
            self.status_bar.showMessage(f"Connected to {port}")
            self.log_message(f"Connected to Arduino on {port}")
        else:
            QMessageBox.critical(self, "Connection Error", "Failed to connect to Arduino!")
    
    def disconnect_arduino(self):
        """Disconnect from Arduino"""
        self.data_collector.disconnect()
        self.connection_status.setText("Disconnected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        self.measuring_status.setText("Not Measuring")
        self.measuring_status.setStyleSheet("color: gray;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.status_bar.showMessage("Disconnected")
        self.log_message("Disconnected from Arduino")
    
    def set_mode(self, mode):
        """Set measurement mode"""
        self.measuring_status.setText(f"Measuring {mode.upper()}")
        self.measuring_status.setStyleSheet("color: blue; font-weight: bold;")
        self.log_message(f"Mode changed to: {mode}")
        
        # Send command to Arduino
        if self.data_collector.serial_port:
            self.data_collector.serial_port.write(f"MODE:{mode}\n".encode())
    
    def test_continuity(self):
        """Test continuity (beep if resistance < 50Ω)"""
        self.measuring_status.setText("Continuity Test")
        self.measuring_status.setStyleSheet("color: purple; font-weight: bold;")
        self.log_message("Continuity test started")
        
        if self.data_collector.serial_port:
            self.data_collector.serial_port.write("MODE:continuity\n".encode())
    
    def set_auto_range(self):
        """Enable auto ranging"""
        self.manual_range_combo.setEnabled(False)
        self.log_message("Auto range enabled")
        
        if self.data_collector.serial_port:
            self.data_collector.serial_port.write("RANGE:auto\n".encode())
    
    def calibrate(self):
        """Calibrate the multimeter"""
        value, ok = QMessageBox.getDouble(self, "Calibration", 
                                         "Enter known voltage for calibration:",
                                         5.0, 0.1, 30.0, 2)
        if ok:
            self.data_collector.calibrate(value)
            self.log_message(f"Calibrated with {value}V reference")
    
    def zero_offset(self):
        """Zero the offset"""
        if self.data_collector.serial_port:
            self.data_collector.serial_port.write("ZERO\n".encode())
            self.log_message("Zero offset applied")
    
    def update_measurements(self, voltage, current, resistance, temperature):
        """Update measurement displays"""
        self.voltage_display.update_value(voltage)
        self.current_display.update_value(current)
        self.resistance_display.update_value(resistance)
        self.temperature_display.update_value(temperature)
        
        # Update graphs
        self.voltage_graph.add_data(voltage)
        self.current_graph.add_data(current)
        self.resistance_graph.add_data(resistance)
        
        # Log data periodically (every 10th reading to avoid spam)
        if hasattr(self, '_log_counter'):
            self._log_counter += 1
        else:
            self._log_counter = 0
            
        if self._log_counter % 10 == 0:
            self.log_message(f"V:{voltage:.3f}V I:{current:.6f}A R:{resistance:.1f}Ω T:{temperature:.1f}°C")
    
    def log_message(self, message):
        """Add message to log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """Clear the log text"""
        self.log_text.clear()
    
    def export_data(self):
        """Export measurement data to file"""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("Timestamp,Voltage (V),Current (A),Resistance (Ω),Temperature (°C)\n")
                    # Export from displays history
                    for i in range(len(self.voltage_display.history)):
                        timestamp = i * 0.1  # Assuming 100ms intervals
                        v = self.voltage_display.history[i] if i < len(self.voltage_display.history) else 0
                        c = self.current_display.history[i] if i < len(self.current_display.history) else 0
                        r = self.resistance_display.history[i] if i < len(self.resistance_display.history) else 0
                        t = self.temperature_display.history[i] if i < len(self.temperature_display.history) else 0
                        f.write(f"{timestamp:.1f},{v:.6f},{c:.9f},{r:.2f},{t:.2f}\n")
                
                self.log_message(f"Data exported to {filename}")
                QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")
    
    def open_website(self):
        """Open the project website"""
        import webbrowser
        webbrowser.open("https://github.com/yourusername/arduino-multimeter")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Arduino Multimeter Software v1.0\n\n"
                         "Professional multimeter application for Arduino\n"
                         "Measures voltage, current, resistance, and temperature\n\n"
                         "Features:\n"
                         "• Real-time measurement display\n"
                         "• Data logging and export\n"
                         "• Continuity testing\n"
                         "• Auto-ranging\n"
                         "• Calibration support")
    
    def closeEvent(self, event):
        """Handle application close"""
        self.data_collector.disconnect()
        event.accept()

def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application style
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, Qt.black)
    app.setPalette(palette)
    
    window = MultimeterGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()