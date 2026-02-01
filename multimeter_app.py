from pc_software.desktop.multimeter_app import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.multimeter_app", run_name="__main__")


class MultimeterSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Multimeter Software")
        self.root.geometry("900x700")
        
        # Measurement parameters
        self.measuring = False
        self.measurement_mode = tk.StringVar(value="Voltage")
        self.voltage_range = tk.StringVar(value="0-10V")
        self.current_range = tk.StringVar(value="0-1A")
        self.resistance_range = tk.StringVar(value="0-1kΩ")
        
        # Data storage
        self.measurements = deque(maxlen=100)
        self.time_stamps = deque(maxlen=100)
        self.data_log = []
        
        # Load configuration
        self.load_config()
        
        # Create GUI
        self.create_widgets()
        
        # Start measurement thread
        self.measurement_thread = None
        
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.voltage_offset = config.get('voltage_offset', 0.0)
                self.current_offset = config.get('current_offset', 0.0)
                self.resistance_offset = config.get('resistance_offset', 0.0)
        except:
            self.voltage_offset = 0.0
            self.current_offset = 0.0
            self.resistance_offset = 0.0
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Measurement Mode
        ttk.Label(control_frame, text="Measurement Mode:").grid(row=0, column=0, padx=5)
        mode_combo = ttk.Combobox(control_frame, textvariable=self.measurement_mode, 
                                  values=["Voltage", "Current", "Resistance"], width=15)
        mode_combo.grid(row=0, column=1, padx=5)
        mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
        # Range Selection
        ttk.Label(control_frame, text="Range:").grid(row=0, column=2, padx=5)
        self.range_combo = ttk.Combobox(control_frame, textvariable=self.voltage_range, 
                                        values=["0-1V", "0-10V", "0-50V", "0-100V"], width=15)
        self.range_combo.grid(row=0, column=3, padx=5)
        
        # Control Buttons
        self.start_btn = ttk.Button(control_frame, text="Start Measurement", 
                                    command=self.toggle_measurement)
        self.start_btn.grid(row=0, column=4, padx=5)
        
        ttk.Button(control_frame, text="Clear Data", command=self.clear_data).grid(row=0, column=5, padx=5)
        ttk.Button(control_frame, text="Export Data", command=self.export_data).grid(row=0, column=6, padx=5)
        ttk.Button(control_frame, text="Calibrate", command=self.calibrate).grid(row=0, column=7, padx=5)
        
        # Display Panel
        display_frame = ttk.LabelFrame(main_frame, text="Measurement Display", padding="10")
        display_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Digital Display
        self.display_var = tk.StringVar(value="0.000")
        self.unit_var = tk.StringVar(value="V")
        
        display_font = ('Digital', 24, 'bold')
        self.digital_display = ttk.Label(display_frame, textvariable=self.display_var, 
                                         font=display_font, foreground="blue")
        self.digital_display.grid(row=0, column=0, padx=20, pady=10)
        
        self.unit_label = ttk.Label(display_frame, textvariable=self.unit_var, 
                                    font=('Arial', 18, 'bold'))
        self.unit_label.grid(row=0, column=1, padx=5, pady=10)
        
        # Status Indicator
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(display_frame, textvariable=self.status_var, 
                                      font=('Arial', 10))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Graph Panel
        graph_frame = ttk.LabelFrame(main_frame, text="Real-time Graph", padding="10")
        graph_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Value')
        self.ax.set_title('Measurement History')
        self.ax.grid(True, alpha=0.3)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Statistics Panel
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.stats_var = tk.StringVar(value="Min: 0.000 | Max: 0.000 | Avg: 0.000 | Std: 0.000")
        ttk.Label(stats_frame, textvariable=self.stats_var, font=('Arial', 10)).pack()
        
    def on_mode_change(self, event=None):
        mode = self.measurement_mode.get()
        if mode == "Voltage":
            self.range_combo['values'] = ["0-1V", "0-10V", "0-50V", "0-100V"]
            self.range_combo.set("0-10V")
            self.unit_var.set("V")
        elif mode == "Current":
            self.range_combo['values'] = ["0-1mA", "0-10mA", "0-100mA", "0-1A", "0-10A"]
            self.range_combo.set("0-1A")
            self.unit_var.set("A")
        elif mode == "Resistance":
            self.range_combo['values'] = ["0-100Ω", "0-1kΩ", "0-10kΩ", "0-100kΩ", "0-1MΩ"]
            self.range_combo.set("0-1kΩ")
            self.unit_var.set("Ω")
    
    def get_range_value(self, range_str):
        if "V" in range_str:
            if "1V" in range_str: return 1.0
            elif "10V" in range_str: return 10.0
            elif "50V" in range_str: return 50.0
            elif "100V" in range_str: return 100.0
        elif "A" in range_str:
            if "1mA" in range_str: return 0.001
            elif "10mA" in range_str: return 0.01
            elif "100mA" in range_str: return 0.1
            elif "1A" in range_str: return 1.0
            elif "10A" in range_str: return 10.0
        elif "Ω" in range_str:
            if "100Ω" in range_str: return 100.0
            elif "1kΩ" in range_str: return 1000.0
            elif "10kΩ" in range_str: return 10000.0
            elif "100kΩ" in range_str: return 100000.0
            elif "1MΩ" in range_str: return 1000000.0
        return 10.0
    
    def simulate_measurement(self):
        mode = self.measurement_mode.get()
        range_val = self.get_range_value(self.range_combo.get())
        
        # Simulate measurement with noise
        if mode == "Voltage":
            base_value = random.uniform(0.1, 0.9) * range_val
            noise = random.gauss(0, range_val * 0.01)
            value = base_value + noise + self.voltage_offset
        elif mode == "Current":
            base_value = random.uniform(0.1, 0.9) * range_val
            noise = random.gauss(0, range_val * 0.01)
            value = base_value + noise + self.current_offset
        else:  # Resistance
            base_value = random.uniform(0.1, 0.9) * range_val
            noise = random.gauss(0, range_val * 0.01)
            value = base_value + noise + self.resistance_offset
        
        return max(0, min(value, range_val))
    
    def measurement_loop(self):
        start_time = time.time()
        
        while self.measuring:
            value = self.simulate_measurement()
            current_time = time.time() - start_time
            
            # Update data
            self.measurements.append(value)
            self.time_stamps.append(current_time)
            
            # Log data
            self.data_log.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'mode': self.measurement_mode.get(),
                'range': self.range_combo.get(),
                'value': value,
                'unit': self.unit_var.get()
            })
            
            # Update display
            self.root.after(0, self.update_display, value)
            
            time.sleep(0.1)  # 10 Hz sampling rate
    
    def update_display(self, value):
        self.display_var.set(f"{value:.3f}")
        self.status_var.set(f"Measuring... Samples: {len(self.measurements)}")
        
        # Update graph
        if len(self.measurements) > 1:
            self.ax.clear()
            self.ax.plot(list(self.time_stamps), list(self.measurements), 'b-', linewidth=2)
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel(f'{self.measurement_mode.get()} ({self.unit_var.get()})')
            self.ax.set_title('Real-time Measurement')
            self.ax.grid(True, alpha=0.3)
            self.canvas.draw()
        
        # Update statistics
        if len(self.measurements) > 0:
            data_array = np.array(list(self.measurements))
            min_val = np.min(data_array)
            max_val = np.max(data_array)
            avg_val = np.mean(data_array)
            std_val = np.std(data_array)
            
            stats_text = f"Min: {min_val:.3f} | Max: {max_val:.3f} | Avg: {avg_val:.3f} | Std: {std_val:.3f}"
            self.stats_var.set(stats_text)
    
    def toggle_measurement(self):
        if not self.measuring:
            self.measuring = True
            self.start_btn.config(text="Stop Measurement")
            self.status_var.set("Starting measurement...")
            
            # Start measurement thread
            self.measurement_thread = threading.Thread(target=self.measurement_loop, daemon=True)
            self.measurement_thread.start()
        else:
            self.measuring = False
            self.start_btn.config(text="Start Measurement")
            self.status_var.set("Measurement stopped")
    
    def clear_data(self):
        self.measurements.clear()
        self.time_stamps.clear()
        self.data_log.clear()
        self.display_var.set("0.000")
        self.status_var.set("Data cleared")
        
        # Clear graph
        self.ax.clear()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Value')
        self.ax.set_title('Measurement History')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        self.stats_var.set("Min: 0.000 | Max: 0.000 | Avg: 0.000 | Std: 0.000")
    
    def export_data(self):
        if not self.data_log:
            messagebox.showwarning("No Data", "No data to export!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = ['timestamp', 'mode', 'range', 'value', 'unit']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    writer.writerows(self.data_log)
                
                messagebox.showinfo("Export Successful", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting data: {str(e)}")
    
    def calibrate(self):
        calibrate_window = tk.Toplevel(self.root)
        calibrate_window.title("Calibration")
        calibrate_window.geometry("300x200")
        
        ttk.Label(calibrate_window, text="Calibration Offsets", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Voltage offset
        ttk.Label(calibrate_window, text="Voltage Offset:").pack()
        voltage_offset_var = tk.StringVar(value=str(self.voltage_offset))
        ttk.Entry(calibrate_window, textvariable=voltage_offset_var).pack()
        
        # Current offset
        ttk.Label(calibrate_window, text="Current Offset:").pack()
        current_offset_var = tk.StringVar(value=str(self.current_offset))
        ttk.Entry(calibrate_window, textvariable=current_offset_var).pack()
        
        # Resistance offset
        ttk.Label(calibrate_window, text="Resistance Offset:").pack()
        resistance_offset_var = tk.StringVar(value=str(self.resistance_offset))
        ttk.Entry(calibrate_window, textvariable=resistance_offset_var).pack()
        
        def save_calibration():
            try:
                config = {
                    'voltage_offset': float(voltage_offset_var.get()),
                    'current_offset': float(current_offset_var.get()),
                    'resistance_offset': float(resistance_offset_var.get())
                }
                
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                
                self.load_config()
                messagebox.showinfo("Success", "Calibration saved successfully!")
                calibrate_window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid offset values!")
        
        ttk.Button(calibrate_window, text="Save", command=save_calibration).pack(pady=10)

def main():
    root = tk.Tk()
    app = MultimeterSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()