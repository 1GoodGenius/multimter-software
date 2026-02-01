import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from datetime import datetime
import threading
import time
import queue
import serial
import serial.tools.list_ports

class DigitalMultimeterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Multimeter")
        self.root.geometry("1000x700")
        
        self.serial_port = None
        self.measurement_queue = queue.Queue()
        self.is_measuring = False
        self.measurement_data = {'time': [], 'value': []}
        self.current_mode = 'DC Voltage'
        
        self.setup_gui()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.setup_connection_frame(main_frame)
        self.setup_measurement_frame(main_frame)
        self.setup_graph_frame(main_frame)
        self.setup_control_frame(main_frame)
        
    def setup_connection_frame(self, parent):
        conn_frame = ttk.LabelFrame(parent, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=5)
        
        self.refresh_ports_btn = ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports)
        self.refresh_ports_btn.grid(row=0, column=2, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, padx=5)
        
        self.connection_status = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.connection_status.grid(row=0, column=4, padx=20)
        
        self.refresh_ports()
        
    def setup_measurement_frame(self, parent):
        measure_frame = ttk.LabelFrame(parent, text="Measurement", padding="10")
        measure_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        self.display_var = tk.StringVar(value="0.000")
        self.unit_var = tk.StringVar(value="V")
        
        self.display_label = ttk.Label(measure_frame, textvariable=self.display_var, 
                                     font=('Digital-7', 48, 'bold'))
        self.display_label.grid(row=0, column=0, padx=20, pady=10)
        
        self.unit_label = ttk.Label(measure_frame, textvariable=self.unit_var, 
                                   font=('Arial', 24))
        self.unit_label.grid(row=0, column=1, padx=10, pady=10)
        
        mode_frame = ttk.Frame(measure_frame)
        mode_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Label(mode_frame, text="Mode:").grid(row=0, column=0, padx=5)
        self.mode_var = tk.StringVar(value=self.current_mode)
        
        modes = ['DC Voltage', 'AC Voltage', 'DC Current', 'AC Current', 'Resistance', 'Continuity']
        self.mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=modes, width=15)
        self.mode_combo.grid(row=0, column=1, padx=5)
        self.mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
        ttk.Button(mode_frame, text="Zero", command=self.zero_measurement).grid(row=0, column=2, padx=5)
        ttk.Button(mode_frame, text="Hold", command=self.toggle_hold).grid(row=0, column=3, padx=5)
        
    def setup_graph_frame(self, parent):
        graph_frame = ttk.LabelFrame(parent, text="Data Visualization", padding="5")
        graph_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Value')
        self.ax.set_title('Real-time Measurement')
        self.ax.grid(True, alpha=0.3)
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def setup_control_frame(self, parent):
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="5")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(control_frame, text="Start Measurement", command=self.start_measurement).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Stop Measurement", command=self.stop_measurement).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Clear Data", command=self.clear_data).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Save Data", command=self.save_data).grid(row=0, column=3, padx=5)
        
        self.record_status = ttk.Label(control_frame, text="Status: Idle", foreground="black")
        self.record_status.grid(row=0, column=4, padx=20)
        
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
            
    def toggle_connection(self):
        if self.serial_port is None:
            try:
                port = self.port_var.get()
                self.serial_port = serial.Serial(port, 9600, timeout=1)
                self.connect_btn.config(text="Disconnect")
                self.connection_status.config(text="Connected", foreground="green")
                messagebox.showinfo("Success", f"Connected to {port}")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
        else:
            self.serial_port.close()
            self.serial_port = None
            self.connect_btn.config(text="Connect")
            self.connection_status.config(text="Disconnected", foreground="red")
            
    def on_mode_change(self, event=None):
        self.current_mode = self.mode_var.get()
        units = {
            'DC Voltage': 'V', 'AC Voltage': 'V',
            'DC Current': 'A', 'AC Current': 'A',
            'Resistance': 'Ω', 'Continuity': 'Ω'
        }
        self.unit_var.set(units.get(self.current_mode, ''))
        self.update_graph()
        
    def zero_measurement(self):
        self.display_var.set("0.000")
        
    def toggle_hold(self):
        if hasattr(self, 'is_holding'):
            self.is_holding = not self.is_holding
        else:
            self.is_holding = True
            
    def start_measurement(self):
        if not self.serial_port:
            messagebox.showwarning("Warning", "Please connect to a device first")
            return
            
        self.is_measuring = True
        self.record_status.config(text="Status: Recording", foreground="green")
        self.measurement_thread = threading.Thread(target=self.measurement_loop)
        self.measurement_thread.daemon = True
        self.measurement_thread.start()
        self.root.after(100, self.update_display)
        
    def stop_measurement(self):
        self.is_measuring = False
        self.record_status.config(text="Status: Idle", foreground="black")
        
    def measurement_loop(self):
        start_time = time.time()
        while self.is_measuring:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode().strip()
                    if line:
                        value = self.parse_measurement(line)
                        if value is not None:
                            current_time = time.time() - start_time
                            self.measurement_queue.put((current_time, value))
            except Exception as e:
                print(f"Measurement error: {e}")
            time.sleep(0.1)
            
    def parse_measurement(self, line):
        try:
            value = float(line)
            return value
        except ValueError:
            return None
            
    def update_display(self):
        if self.is_measuring:
            try:
                while not self.measurement_queue.empty():
                    timestamp, value = self.measurement_queue.get_nowait()
                    self.measurement_data['time'].append(timestamp)
                    self.measurement_data['value'].append(value)
                    
                    if not hasattr(self, 'is_holding') or not self.is_holding:
                        self.display_var.set(f"{value:.3f}")
                        
                self.update_graph()
                self.root.after(100, self.update_display)
            except queue.Empty:
                pass
                
    def update_graph(self):
        if self.measurement_data['time']:
            self.ax.clear()
            self.ax.plot(self.measurement_data['time'], self.measurement_data['value'], 'b-')
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel(f'Value ({self.unit_var.get()})')
            self.ax.set_title(f'{self.current_mode} Measurement')
            self.ax.grid(True, alpha=0.3)
            self.canvas.draw()
            
    def clear_data(self):
        self.measurement_data = {'time': [], 'value': []}
        self.display_var.set("0.000")
        self.update_graph()
        
    def save_data(self):
        if not self.measurement_data['time']:
            messagebox.showwarning("Warning", "No data to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"multimeter_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            df = pd.DataFrame({
                'Time (s)': self.measurement_data['time'],
                f'{self.current_mode} ({self.unit_var.get()})': self.measurement_data['value']
            })
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", f"Data saved to {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalMultimeterApp(root)
    root.mainloop()