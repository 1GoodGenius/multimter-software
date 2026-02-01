from pc_software.desktop.main import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.main", run_name="__main__")
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Multimeter")
        self.root.geometry("900x700")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize simulator
        self.simulator = MultimeterSimulator()
        
        # Variables
        self.current_value = 0.0
        self.max_value = 600.0  # Default range for AC voltage
        self.measurement_mode = "DC Voltage"
        self.serial_port = None
        self.running = False
        self.hold_active = False
        self.hold_value = 0.0
        
        # Create GUI
        self.setup_gui()
        self.draw_analog_meter()
        self.update_needle(0)
        
        # Start with simulation
        self.start_simulation()
    
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top panel - Large digital display
        top_frame = tk.Frame(main_frame, bg='#1a1a1a')
        top_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Digital display frame
        display_frame = tk.Frame(top_frame, bg='#000000', relief=tk.SUNKEN, bd=3)
        display_frame.pack(pady=10)
        
        # Large 7-segment style display
        self.digital_display = tk.Label(display_frame, text="0.000", 
                                      font=('Courier New', 72, 'bold'),
                                      fg='#00ff00', bg='#000000', width=12)
        self.digital_display.pack(padx=30, pady=20)
        
        # Unit and mode display
        info_frame = tk.Frame(top_frame, bg='#1a1a1a')
        info_frame.pack()
        
        self.mode_display = tk.Label(info_frame, text="DC Voltage", 
                                   font=('Arial', 18, 'bold'),
                                   fg='#ffffff', bg='#1a1a1a')
        self.mode_display.pack(side=tk.LEFT, padx=10)
        
        self.unit_display = tk.Label(info_frame, text="V", 
                                   font=('Arial', 18, 'bold'),
                                   fg='#ffff00', bg='#1a1a1a')
        self.unit_display.pack(side=tk.LEFT, padx=10)
        
        self.range_display = tk.Label(info_frame, text="Auto", 
                                    font=('Arial', 16),
                                    fg='#cccccc', bg='#1a1a1a')
        self.range_display.pack(side=tk.LEFT, padx=10)
        
        # Middle panel - Analog meter
        middle_frame = tk.Frame(main_frame, bg='#1a1a1a')
        middle_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for analog meter
        self.canvas = tk.Canvas(middle_frame, width=400, height=300, bg='#2a2a2a', highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=20)
        
        # Right panel - Controls
        right_frame = tk.Frame(middle_frame, bg='#1a1a1a', width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))
        right_frame.pack_propagate(False)
        
        # Measurement mode selection
        mode_frame = tk.LabelFrame(right_frame, text="Measurement Mode", 
                                  font=('Arial', 12, 'bold'),
                                  fg='#ffffff', bg='#1a1a1a')
        mode_frame.pack(fill=tk.X, pady=10)
        
        self.mode_var = tk.StringVar(value="DC Voltage")
        modes = ["DC Voltage", "AC Voltage", "DC Current", "AC Current", 
                "Resistance", "Capacitance", "Continuity", "Diode Test", "Frequency", "Temperature"]
        
        # Create mode buttons in grid
        for i, mode in enumerate(modes):
            row = i // 2
            col = i % 2
            tk.Radiobutton(mode_frame, text=mode, variable=self.mode_var, value=mode,
                          font=('Arial', 10), fg='#ffffff', bg='#1a1a1a',
                          selectcolor='#1a1a1a', activebackground='#1a1a1a',
                          command=self.change_mode).grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
        
        # Range selection
        range_frame = tk.LabelFrame(right_frame, text="Range", 
                                  font=('Arial', 12, 'bold'),
                                  fg='#ffffff', bg='#1a1a1a')
        range_frame.pack(fill=tk.X, pady=10)
        
        self.range_var = tk.StringVar(value="Auto")
        ranges = ["Auto", "600V", "200V", "20V", "2V", "600mV", "200mV"]
        
        for range_val in ranges:
            tk.Radiobutton(range_frame, text=range_val, variable=self.range_var, value=range_val,
                          font=('Arial', 10), fg='#ffffff', bg='#1a1a1a',
                          selectcolor='#1a1a1a', activebackground='#1a1a1a',
                          command=self.change_range).pack(anchor=tk.W, padx=10, pady=2)
        
        # Port selection
        port_frame = tk.LabelFrame(right_frame, text="Serial Port", 
                                 font=('Arial', 12, 'bold'),
                                 fg='#ffffff', bg='#1a1a1a')
        port_frame.pack(fill=tk.X, pady=10)
        
        self.port_combo = ttk.Combobox(port_frame, values=self.get_serial_ports(), width=20)
        self.port_combo.pack(padx=10, pady=5)
        
        # Control buttons
        button_frame = tk.Frame(right_frame, bg='#1a1a1a')
        button_frame.pack(fill=tk.X, pady=20)
        
        self.connect_btn = tk.Button(button_frame, text="Connect", 
                                    font=('Arial', 10, 'bold'),
                                    bg='#4CAF50', fg='white',
                                    command=self.toggle_connection)
        self.connect_btn.pack(fill=tk.X, padx=10, pady=5)
        
        self.zero_btn = tk.Button(button_frame, text="Zero", 
                                font=('Arial', 10, 'bold'),
                                bg='#FF9800', fg='white',
                                command=self.zero_reading)
        self.zero_btn.pack(fill=tk.X, padx=10, pady=5)
        
        self.hold_btn = tk.Button(button_frame, text="Hold", 
                                 font=('Arial', 10, 'bold'),
                                 bg='#2196F3', fg='white',
                                 command=self.toggle_hold)
        self.hold_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # Status bar
        self.status_label = tk.Label(main_frame, text="Status: Simulation Running", 
                                   font=('Arial', 10), fg='#cccccc', bg='#1a1a1a')
        self.status_label.pack(side=tk.BOTTOM, pady=10)
    
    def get_serial_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ["None"] + ports
    
    def draw_analog_meter(self):
        # Clear canvas
        self.canvas.delete("all")
        
        center_x, center_y = 200, 180
        radius = 120
        
        # Draw outer circle
        self.canvas.create_oval(center_x - radius, center_y - radius,
                               center_x + radius, center_y + radius,
                               outline='#ffffff', width=3, fill='#3a3a3a')
        
        # Draw inner circles
        for r in [100, 80]:
            self.canvas.create_oval(center_x - r, center_y - r,
                                  center_x + r, center_y + r,
                                  outline='#666666', width=1)
        
        # Draw scale markings
        for i in range(0, 61):  # 0 to 60 divisions
            angle = math.radians(-120 + (i * 240 / 60))  # -120 to +120 degrees
            
            # Calculate position
            start_r = radius - 15 if i % 10 == 0 else (radius - 10 if i % 5 == 0 else radius - 5)
            end_r = radius - 3
            
            x1 = center_x + start_r * math.cos(angle)
            y1 = center_y + start_r * math.sin(angle)
            x2 = center_x + end_r * math.cos(angle)
            y2 = center_y + end_r * math.sin(angle)
            
            # Draw marking
            width = 2 if i % 10 == 0 else (1 if i % 5 == 0 else 1)
            color = '#ffffff' if i % 10 == 0 else '#cccccc'
            
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            
            # Add numbers for major divisions
            if i % 10 == 0:
                value = (i / 60) * self.max_value
                text_r = radius - 25
                text_x = center_x + text_r * math.cos(angle)
                text_y = center_y + text_r * math.sin(angle)
                
                self.canvas.create_text(text_x, text_y, text=f"{value:.0f}",
                                      font=('Arial', 10, 'bold'),
                                      fill='#ffffff')
        
        # Draw center hub
        hub_radius = 6
        self.canvas.create_oval(center_x - hub_radius, center_y - hub_radius,
                              center_x + hub_radius, center_y + hub_radius,
                              fill='#ff0000', outline='#ffffff', width=2)
        
        # Create needle (will be updated)
        self.needle = None
    
    def update_needle(self, value):
        if self.needle:
            self.canvas.delete(self.needle)
        
        center_x, center_y = 200, 180
        needle_length = 100
        
        # Calculate angle (-120 to +120 degrees)
        angle = math.radians(-120 + (value / self.max_value) * 240)
        
        # Needle end position
        end_x = center_x + needle_length * math.cos(angle)
        end_y = center_y + needle_length * math.sin(angle)
        
        # Draw needle
        self.needle = self.canvas.create_line(center_x, center_y, end_x, end_y,
                                            fill='#ff0000', width=2, capstyle='round')
        
        # Update digital display
        display_value = self.hold_value if self.hold_active else value
        self.digital_display.config(text=f"{display_value:.3f}")
    
    def change_mode(self):
        self.measurement_mode = self.mode_var.get()
        self.simulator.set_mode(self.measurement_mode)
        self.update_unit_display()
        self.status_label.config(text=f"Status: Mode changed to {self.measurement_mode}")
    
    def change_range(self):
        range_val = self.range_var.get()
        self.simulator.range = range_val.lower()
        
        if range_val == "Auto":
            self.max_value = 600.0
        elif range_val == "600V":
            self.max_value = 600.0
        elif range_val == "200V":
            self.max_value = 200.0
        elif range_val == "20V":
            self.max_value = 20.0
        elif range_val == "2V":
            self.max_value = 2.0
        elif range_val == "600mV":
            self.max_value = 0.6
        elif range_val == "200mV":
            self.max_value = 0.2
        
        self.range_display.config(text=range_val)
        self.draw_analog_meter()
        self.status_label.config(text=f"Status: Range changed to {range_val}")
    
    def update_unit_display(self):
        mode = self.measurement_mode
        if "Voltage" in mode:
            unit = "V"
        elif "Current" in mode:
            unit = "A"
        elif "Resistance" in mode:
            unit = "Ω"
        elif "Capacitance" in mode:
            unit = "F"
        elif "Continuity" in mode:
            unit = "Ω"
        elif "Frequency" in mode:
            unit = "Hz"
        elif "Temperature" in mode:
            unit = "°C"
        elif "Diode" in mode:
            unit = "V"
        else:
            unit = ""
        
        self.unit_display.config(text=unit)
    
    def toggle_connection(self):
        if not self.running:
            selected_port = self.port_combo.get()
            if selected_port and selected_port != "None":
                try:
                    self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
                    self.running = True
                    self.connect_btn.config(text="Disconnect", bg='#f44336')
                    threading.Thread(target=self.read_serial_data, daemon=True).start()
                    self.status_label.config(text=f"Status: Connected to {selected_port}")
                except Exception as e:
                    self.status_label.config(text=f"Status: Failed to connect - {e}")
        else:
            self.running = False
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
            self.connect_btn.config(text="Connect", bg='#4CAF50')
            self.status_label.config(text="Status: Disconnected")
    
    def read_serial_data(self):
        while self.running and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line:
                        try:
                            value = float(line)
                            self.current_value = min(value, self.max_value)
                            self.root.after(0, self.update_display)
                        except ValueError:
                            pass
                time.sleep(0.1)
            except Exception as e:
                self.status_label.config(text=f"Status: Serial error - {e}")
                break
    
    def start_simulation(self):
        self.simulation_running = True
        threading.Thread(target=self.simulate_reading, daemon=True).start()
    
    def simulate_reading(self):
        while self.simulation_running and not self.running:
            # Get simulated reading from the simulator
            value, error = self.simulator.get_measurement()
            
            if error == "OL":
                self.current_value = self.max_value
            elif value is not None:
                # Scale value for display based on mode
                if self.measurement_mode in ["DC Voltage", "AC Voltage"]:
                    self.current_value = value
                elif self.measurement_mode in ["DC Current", "AC Current"]:
                    self.current_value = value * 1000  # Convert to mA for display
                elif self.measurement_mode == "Resistance":
                    self.current_value = min(value, self.max_value)
                elif self.measurement_mode == "Frequency":
                    self.current_value = min(value, self.max_value)
                else:
                    self.current_value = min(value, self.max_value)
            
            if not self.hold_active:
                self.root.after(0, self.update_display)
            time.sleep(0.3)
    
    def update_display(self):
        value = self.hold_value if self.hold_active else self.current_value
        
        # Update analog needle
        self.update_needle(value)
        
        # Update mode display
        self.mode_display.config(text=self.measurement_mode)
    
    def zero_reading(self):
        self.current_value = 0.0
        self.hold_value = 0.0
        self.simulator.reference_values[self.simulator.mode] = 0.0
        self.update_display()
        self.status_label.config(text="Status: Zeroed")
    
    def toggle_hold(self):
        if self.hold_btn['text'] == "Hold":
            self.hold_active = True
            self.hold_value = self.current_value
            self.hold_btn.config(text="Release", bg='#4CAF50')
            self.status_label.config(text="Status: Reading held")
        else:
            self.hold_active = False
            self.hold_btn.config(text="Hold", bg='#2196F3')
            self.status_label.config(text="Status: Reading released")

def main():
    root = tk.Tk()
    app = DigitalMultimeterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()