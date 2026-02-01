from pc_software.desktop.multimeter_gui_new import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.multimeter_gui_new", run_name="__main__")


from keithley_2400 import Keithley2400, MeasurementMode, Measurement
from pc_software.bluetooth import BluetoothManager

logger = logging.getLogger(__name__)

class MultiMeterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Multi-Meter Software")
        self.root.geometry("1200x800")
        
        # Initialize instruments
        self.keithley = Keithley2400()
        self.bluetooth = BluetoothManager()
        
        # Data storage
        self.measurement_history = deque(maxlen=1000)
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Setup GUI
        self.setup_gui()
        self.update_status()
        
        # Start status update timer
        self.root.after(1000, self.periodic_status_update)
    
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Create main frames
        self.create_menu_bar()
        self.create_connection_frame()
        self.create_control_frame()
        self.create_display_frame()
        self.create_plot_frame()
        self.create_status_frame()
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_command(label="Import Settings", command=self.import_settings)
        file_menu.add_command(label="Export Settings", command=self.export_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_connection_frame(self):
        """Connection control frame"""
        conn_frame = ttk.LabelFrame(self.root, text="Instrument Connection", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Keithley connection
        ttk.Label(conn_frame, text="Keithley 2400:").grid(row=0, column=0, sticky="w")
        self.keithley_status_var = tk.StringVar(value="Disconnected")
        ttk.Label(conn_frame, textvariable=self.keithley_status_var).grid(row=0, column=1, sticky="w")
        
        self.keithley_connect_btn = ttk.Button(conn_frame, text="Connect", 
                                              command=self.toggle_keithley_connection)
        self.keithley_connect_btn.grid(row=0, column=2, padx=5)
        
        # Bluetooth connection
        ttk.Label(conn_frame, text="Bluetooth:").grid(row=0, column=3, sticky="w", padx=(20,0))
        self.bluetooth_status_var = tk.StringVar(value="Disconnected")
        ttk.Label(conn_frame, textvariable=self.bluetooth_status_var).grid(row=0, column=4, sticky="w")
        
        self.bluetooth_connect_btn = ttk.Button(conn_frame, text="Scan & Connect", 
                                               command=self.scan_bluetooth_devices)
        self.bluetooth_connect_btn.grid(row=0, column=5, padx=5)
    
    def create_control_frame(self):
        """Measurement control frame"""
        control_frame = ttk.LabelFrame(self.root, text="Measurement Control", padding="10")
        control_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Measurement mode
        ttk.Label(control_frame, text="Mode:").grid(row=0, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="VOLT:DC")
        mode_combo = ttk.Combobox(control_frame, textvariable=self.mode_var, width=15)
        mode_combo['values'] = [mode.value for mode in MeasurementMode]
        mode_combo.grid(row=0, column=1, padx=5)
        
        # Range setting
        ttk.Label(control_frame, text="Range:").grid(row=1, column=0, sticky="w")
        self.range_var = tk.StringVar(value="Auto")
        range_combo = ttk.Combobox(control_frame, textvariable=self.range_var, width=15)
        range_combo['values'] = ["Auto", "2V", "20V", "200V", "2A", "20mA", "200mA"]
        range_combo.grid(row=1, column=1, padx=5)
        
        # Safety limits
        ttk.Label(control_frame, text="Max Voltage (V):").grid(row=2, column=0, sticky="w")
        self.max_voltage_var = tk.StringVar(value="210")
        ttk.Entry(control_frame, textvariable=self.max_voltage_var, width=10).grid(row=2, column=1, padx=5)
        
        ttk.Label(control_frame, text="Max Current (A):").grid(row=3, column=0, sticky="w")
        self.max_current_var = tk.StringVar(value="1.05")
        ttk.Entry(control_frame, textvariable=self.max_current_var, width=10).grid(row=3, column=1, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.single_measure_btn = ttk.Button(button_frame, text="Single Measure", 
                                            command=self.single_measurement)
        self.single_measure_btn.grid(row=0, column=0, padx=5)
        
        self.monitor_btn = ttk.Button(button_frame, text="Start Monitor", 
                                     command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=1, padx=5)
        
        self.output_btn = ttk.Button(button_frame, text="Enable Output", 
                                    command=self.toggle_output)
        self.output_btn.grid(row=0, column=2, padx=5)
        
        # Apply safety limits button
        ttk.Button(control_frame, text="Apply Safety Limits", 
                  command=self.apply_safety_limits).grid(row=5, column=0, columnspan=2, pady=5)
    
    def create_display_frame(self):
        """Current measurement display frame"""
        display_frame = ttk.LabelFrame(self.root, text="Current Measurement", padding="10")
        display_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Large display for current value
        self.value_display_var = tk.StringVar(value="--.--")
        self.value_label = ttk.Label(display_frame, textvariable=self.value_display_var, 
                                    font=("Arial", 48, "bold"))
        self.value_label.grid(row=0, column=0, columnspan=2)
        
        # Unit and mode display
        self.unit_display_var = tk.StringVar(value="V")
        ttk.Label(display_frame, textvariable=self.unit_display_var, 
                 font=("Arial", 24)).grid(row=1, column=0)
        
        self.mode_display_var = tk.StringVar(value="DC Voltage")
        ttk.Label(display_frame, textvariable=self.mode_display_var, 
                 font=("Arial", 12)).grid(row=1, column=1)
        
        # Statistics
        stats_frame = ttk.LabelFrame(display_frame, text="Statistics", padding="5")
        stats_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        self.min_var = tk.StringVar(value="Min: --")
        self.max_var = tk.StringVar(value="Max: --")
        self.avg_var = tk.StringVar(value="Avg: --")
        self.count_var = tk.StringVar(value="Count: 0")
        
        ttk.Label(stats_frame, textvariable=self.min_var).grid(row=0, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.max_var).grid(row=0, column=1, sticky="w")
        ttk.Label(stats_frame, textvariable=self.avg_var).grid(row=1, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.count_var).grid(row=1, column=1, sticky="w")
    
    def create_plot_frame(self):
        """Plotting frame for time series data"""
        plot_frame = ttk.LabelFrame(self.root, text="Time Series Plot", padding="5")
        plot_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 4), dpi=80)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.grid(True, alpha=0.3)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Plot controls
        plot_controls = ttk.Frame(plot_frame)
        plot_controls.pack(fill=tk.X)
        
        ttk.Button(plot_controls, text="Clear Plot", 
                  command=self.clear_plot).pack(side=tk.LEFT, padx=5)
        ttk.Button(plot_controls, text="Save Plot", 
                  command=self.save_plot).pack(side=tk.LEFT, padx=5)
        
        self.auto_scale_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(plot_controls, text="Auto Scale", 
                       variable=self.auto_scale_var).pack(side=tk.LEFT, padx=5)
    
    def create_status_frame(self):
        """Status bar"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.time_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.time_var).pack(side=tk.RIGHT)
        self.update_time()
    
    def toggle_keithley_connection(self):
        """Toggle Keithley connection"""
        if self.keithley.is_connected:
            if self.keithley.disconnect():
                self.keithley_status_var.set("Disconnected")
                self.keithley_connect_btn.config(text="Connect")
                self.status_var.set("Disconnected from Keithley 2400")
        else:
            if self.keithley.connect():
                self.keithley_status_var.set("Connected")
                self.keithley_connect_btn.config(text="Disconnect")
                self.status_var.set("Connected to Keithley 2400")
            else:
                messagebox.showerror("Connection Error", "Failed to connect to Keithley 2400")
    
    def scan_bluetooth_devices(self):
        """Scan and connect to Bluetooth devices"""
        devices = self.bluetooth.scan_devices()
        if not devices:
            messagebox.showinfo("No Devices", "No Bluetooth devices found")
            return
        
        # Create device selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Bluetooth Device")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Available Devices:").pack(pady=5)
        
        device_listbox = tk.Listbox(dialog)
        device_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for device in devices:
            device_listbox.insert(tk.END, f"{device['name']} ({device['address']})")
        
        def connect_selected():
            selection = device_listbox.curselection()
            if selection:
                device = devices[selection[0]]
                if self.bluetooth.connect(device['address']):
                    self.bluetooth_status_var.set(f"Connected to {device['name']}")
                    self.status_var.set(f"Connected to {device['name']}")
                    dialog.destroy()
                else:
                    messagebox.showerror("Connection Error", "Failed to connect to device")
        
        ttk.Button(dialog, text="Connect", command=connect_selected).pack(pady=5)
    
    def apply_safety_limits(self):
        """Apply safety limits to Keithley"""
        try:
            max_voltage = float(self.max_voltage_var.get())
            max_current = float(self.max_current_var.get())
            
            self.keithley.configure_safety_limits(max_voltage, max_current)
            self.status_var.set("Safety limits applied")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values")
    
    def single_measurement(self):
        """Perform a single measurement"""
        if not self.keithley.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to Keithley 2400 first")
            return
        
        try:
            mode = MeasurementMode(self.mode_var.get())
            self.keithley.set_mode(mode)
            
            if self.range_var.get() != "Auto":
                range_value = float(self.range_var.get().replace('V', '').replace('A', ''))
                self.keithley.set_range(range_value)
            
            measurement = self.keithley.measure_single()
            if measurement:
                self.update_display(measurement)
                self.measurement_history.append(measurement)
                self.update_plot()
                self.status_var.set(f"Measurement: {measurement.value:.4f} {measurement.unit}")
            else:
                messagebox.showerror("Measurement Error", "Failed to perform measurement")
        
        except Exception as e:
            messagebox.showerror("Error", f"Measurement failed: {str(e)}")
    
    def toggle_monitoring(self):
        """Toggle continuous monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.monitor_btn.config(text="Start Monitor")
            self.status_var.set("Monitoring stopped")
        else:
            if not self.keithley.is_connected:
                messagebox.showwarning("Not Connected", "Please connect to Keithley 2400 first")
                return
            
            self.is_monitoring = True
            self.monitor_btn.config(text="Stop Monitor")
            self.status_var.set("Monitoring started")
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()
    
    def monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                mode = MeasurementMode(self.mode_var.get())
                self.keithley.set_mode(mode)
                
                measurement = self.keithley.measure_single()
                if measurement:
                    self.measurement_history.append(measurement)
                    self.root.after(0, self.update_display, measurement)
                    self.root.after(0, self.update_plot)
                
                time.sleep(0.5)  # Update every 500ms
            
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(1)
    
    def update_display(self, measurement: Measurement):
        """Update measurement display"""
        self.value_display_var.set(f"{measurement.value:.4f}")
        self.unit_display_var.set(measurement.unit)
        
        # Update mode display
        mode_names = {
            MeasurementMode.VOLTAGE_DC: "DC Voltage",
            MeasurementMode.VOLTAGE_AC: "AC Voltage",
            MeasurementMode.CURRENT_DC: "DC Current",
            MeasurementMode.CURRENT_AC: "AC Current",
            MeasurementMode.RESISTANCE: "Resistance",
            MeasurementMode.RESISTANCE_4WIRE: "4-Wire Resistance",
            MeasurementMode.POWER: "Power"
        }
        self.mode_display_var.set(mode_names.get(measurement.mode, measurement.mode.value))
        
        # Update statistics
        if self.measurement_history:
            values = [m.value for m in self.measurement_history if m.mode == measurement.mode]
            if values:
                self.min_var.set(f"Min: {min(values):.4f}")
                self.max_var.set(f"Max: {max(values):.4f}")
                self.avg_var.set(f"Avg: {sum(values)/len(values):.4f}")
                self.count_var.set(f"Count: {len(values)}")
    
    def update_plot(self):
        """Update time series plot"""
        if not self.measurement_history:
            return
        
        self.ax.clear()
        
        # Group measurements by mode
        mode_data = {}
        for measurement in self.measurement_history:
            if measurement.mode not in mode_data:
                mode_data[measurement.mode] = {'times': [], 'values': []}
            
            relative_time = measurement.timestamp - self.measurement_history[0].timestamp
            mode_data[measurement.mode]['times'].append(relative_time)
            mode_data[measurement.mode]['values'].append(measurement.value)
        
        # Plot each mode
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink']
        for i, (mode, data) in enumerate(mode_data.items()):
            color = colors[i % len(colors)]
            self.ax.plot(data['times'], data['values'], 
                        label=mode.value, color=color, linewidth=2)
        
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Value")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        if self.auto_scale_var.get():
            self.ax.relim()
            self.ax.autoscale_view()
        
        self.canvas.draw()
    
    def clear_plot(self):
        """Clear plot data"""
        self.measurement_history.clear()
        self.ax.clear()
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        self.status_var.set("Plot cleared")
    
    def save_plot(self):
        """Save plot to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.fig.savefig(filename, dpi=150, bbox_inches='tight')
            self.status_var.set(f"Plot saved to {filename}")
    
    def toggle_output(self):
        """Toggle Keithley output"""
        if not self.keithley.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to Keithley 2400 first")
            return
        
        current_state = self.output_btn.cget("text") == "Disable Output"
        if self.keithley.enable_output(not current_state):
            self.output_btn.config(text="Disable Output" if not current_state else "Enable Output")
            self.status_var.set(f"Output {'enabled' if not current_state else 'disabled'}")
        else:
            messagebox.showerror("Error", "Failed to toggle output state")
    
    def export_data(self):
        """Export measurement data to CSV"""
        if not self.measurement_history:
            messagebox.showinfo("No Data", "No measurement data to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'mode', 'value', 'unit']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for measurement in self.measurement_history:
                    writer.writerow({
                        'timestamp': datetime.fromtimestamp(measurement.timestamp).isoformat(),
                        'mode': measurement.mode.value,
                        'value': measurement.value,
                        'unit': measurement.unit
                    })
            
            self.status_var.set(f"Data exported to {filename}")
    
    def export_settings(self):
        """Export current settings to JSON"""
        settings = {
            'mode': self.mode_var.get(),
            'range': self.range_var.get(),
            'max_voltage': self.max_voltage_var.get(),
            'max_current': self.max_current_var.get(),
            'auto_scale': self.auto_scale_var.get()
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(settings, f, indent=2)
            self.status_var.set(f"Settings exported to {filename}")
    
    def import_settings(self):
        """Import settings from JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    settings = json.load(f)
                
                self.mode_var.set(settings.get('mode', 'VOLT:DC'))
                self.range_var.set(settings.get('range', 'Auto'))
                self.max_voltage_var.set(settings.get('max_voltage', '210'))
                self.max_current_var.set(settings.get('max_current', '1.05'))
                self.auto_scale_var.set(settings.get('auto_scale', True))
                
                self.status_var.set(f"Settings imported from {filename}")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import settings: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Professional Multi-Meter Software
        
Version 1.0

A comprehensive instrument control application for
Keithley 2400 SourceMeter and compatible devices.

Features:
• Real-time measurement monitoring
• Multiple measurement modes
• Data logging and export
• Safety limit protection
• Bluetooth device support
• Time series plotting

© 2024 Professional Instruments
"""
        messagebox.showinfo("About", about_text)
    
    def update_status(self):
        """Update connection status displays"""
        # Update Keithley status
        if self.keithley.is_connected:
            status = self.keithley.get_status()
            self.keithley_status_var.set(f"Connected - {status.get('idn', '')[:30]}...")
        else:
            self.keithley_status_var.set("Disconnected")
        
        # Update Bluetooth status
        bt_status = self.bluetooth.get_connection_status()
        if bt_status['connected']:
            self.bluetooth_status_var.set(f"Connected - {bt_status['device']}")
        else:
            self.bluetooth_status_var.set("Disconnected")
    
    def periodic_status_update(self):
        """Periodic status update timer"""
        self.update_status()
        self.root.after(1000, self.periodic_status_update)
    
    def update_time(self):
        """Update current time display**
        self.time_var.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.root.after(1000, self.update_time)
    
    def on_closing(self):
        """Clean up when closing the application"""
        if self.is_monitoring:
            self.is_monitoring = False
        
        if self.keithley.is_connected:
            self.keithley.disconnect()
        
        self.bluetooth.disconnect()
        self.root.destroy()

def main():
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    app = MultiMeterGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()