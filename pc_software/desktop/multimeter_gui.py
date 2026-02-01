import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import math

class DigitalMultimeter:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Multimeter")
        self.root.geometry("900x700")
        self.root.configure(bg='#1a1a1a')
        
        # Measurement variables
        self.current_value = 0.0
        self.measurement_mode = tk.StringVar(value="DC Voltage")
        self.current_range = tk.StringVar(value="Auto")
        self.hold_active = tk.BooleanVar(value=False)
        self.relative_active = tk.BooleanVar(value=False)
        self.minmax_active = tk.BooleanVar(value=False)
        self.zero_offset = 0.0
        self.relative_value = 0.0
        self.held_value = 0.0
        
        # Min/Max tracking
        self.min_value = float('inf')
        self.max_value = float('-inf')
        
        # Simulation
        self.running = True
        self.simulation_thread = threading.Thread(target=self.simulate_readings, daemon=True)
        self.simulation_thread.start()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top section - Display
        display_frame = tk.Frame(main_frame, bg='#000000', relief=tk.SUNKEN, bd=3)
        display_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Main digital display
        self.display_label = tk.Label(display_frame, text="0.000", 
                                     font=("Digital-7", 72, "bold"),
                                     fg="#00ff00", bg="#000000")
        self.display_label.pack(pady=20)
        
        # Unit and mode display
        info_frame = tk.Frame(display_frame, bg="#000000")
        info_frame.pack(pady=(0, 20))
        
        self.unit_label = tk.Label(info_frame, text="V", 
                                  font=("Arial", 24, "bold"),
                                  fg="#00ff00", bg="#000000")
        self.unit_label.pack(side=tk.LEFT, padx=20)
        
        self.mode_display = tk.Label(info_frame, textvariable=self.measurement_mode,
                                   font=("Arial", 14),
                                   fg="#00ff00", bg="#000000")
        self.mode_display.pack(side=tk.LEFT, padx=20)
        
        self.range_display = tk.Label(info_frame, textvariable=self.current_range,
                                     font=("Arial", 14),
                                     fg="#00ff00", bg="#000000")
        self.range_display.pack(side=tk.LEFT, padx=20)
        
        # Status indicators
        self.status_frame = tk.Frame(display_frame, bg="#000000")
        self.status_frame.pack(pady=(0, 10))
        
        self.hold_indicator = tk.Label(self.status_frame, text="",
                                      font=("Arial", 12, "bold"),
                                      fg="#ff0000", bg="#000000")
        self.hold_indicator.pack(side=tk.LEFT, padx=5)
        
        self.rel_indicator = tk.Label(self.status_frame, text="",
                                    font=("Arial", 12, "bold"),
                                    fg="#ff0000", bg="#000000")
        self.rel_indicator.pack(side=tk.LEFT, padx=5)
        
        self.minmax_indicator = tk.Label(self.status_frame, text="",
                                       font=("Arial", 12, "bold"),
                                       fg="#ff0000", bg="#000000")
        self.minmax_indicator.pack(side=tk.LEFT, padx=5)
        
        # Min/Max display frame (initially hidden)
        self.minmax_frame = tk.Frame(main_frame, bg='#1a1a1a')
        
        self.min_label = tk.Label(self.minmax_frame, text="MIN: ---",
                                 font=("Arial", 14),
                                 fg="#00ff00", bg="#1a1a1a")
        self.min_label.pack(side=tk.LEFT, padx=10)
        
        self.max_label = tk.Label(self.minmax_frame, text="MAX: ---",
                                 font=("Arial", 14),
                                 fg="#00ff00", bg="#1a1a1a")
        self.max_label.pack(side=tk.LEFT, padx=10)
        
        # Control panels container
        controls_container = tk.Frame(main_frame, bg='#1a1a1a')
        controls_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Measurement modes
        mode_frame = tk.LabelFrame(controls_container, text="Measurement Mode",
                                 font=("Arial", 12, "bold"),
                                 fg="#ffffff", bg="#1a1a1a")
        mode_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        modes = [
            ("DC Voltage", "V"),
            ("AC Voltage", "V~"),
            ("DC Current", "A"),
            ("AC Current", "A~"),
            ("Resistance", "Ω"),
            ("Continuity", "•)))"),
            ("Diode Test", "D"),
            ("Capacitance", "C"),
            ("Frequency", "Hz"),
            ("Temperature", "°C")
        ]
        
        for i, (mode, symbol) in enumerate(modes):
            btn = tk.Button(mode_frame, text=f"{mode}\n{symbol}", width=12, height=2,
                           command=lambda m=mode: self.set_mode(m),
                           bg="#333333", fg="#ffffff", font=("Arial", 9),
                           relief=tk.RAISED, bd=2)
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
        
        # Middle panel - Range selection
        range_frame = tk.LabelFrame(controls_container, text="Range",
                                   font=("Arial", 12, "bold"),
                                   fg="#ffffff", bg="#1a1a1a")
        range_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        ranges = [
            "Auto", "600V", "200V", "20V", "2V", "600mV", "200mV",
            "10A", "20A", "200mA", "20mA", "2000mA",
            "20MΩ", "2MΩ", "200kΩ", "20kΩ", "2kΩ", "200Ω", "2kΩ"
        ]
        
        for i, range_val in enumerate(ranges):
            btn = tk.Button(range_frame, text=range_val, width=8,
                           command=lambda r=range_val: self.set_range(r),
                           bg="#333333", fg="#ffffff", font=("Arial", 9))
            btn.grid(row=i//6, column=i%6, padx=2, pady=2, sticky="ew")
        
        # Right panel - Function buttons
        func_frame = tk.LabelFrame(controls_container, text="Functions",
                                  font=("Arial", 12, "bold"),
                                  fg="#ffffff", bg="#1a1a1a")
        func_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Function buttons
        self.hold_btn = tk.Button(func_frame, text="HOLD", width=12, height=2,
                                 command=self.toggle_hold,
                                 bg="#333333", fg="#ffffff", font=("Arial", 10, "bold"))
        self.hold_btn.pack(pady=5)
        
        self.minmax_btn = tk.Button(func_frame, text="MIN/MAX", width=12, height=2,
                                   command=self.toggle_minmax,
                                   bg="#333333", fg="#ffffff", font=("Arial", 10, "bold"))
        self.minmax_btn.pack(pady=5)
        
        zero_btn = tk.Button(func_frame, text="ZERO", width=12, height=2,
                            command=self.set_zero,
                            bg="#333333", fg="#ffffff", font=("Arial", 10, "bold"))
        zero_btn.pack(pady=5)
        
        self.rel_btn = tk.Button(func_frame, text="RELATIVE", width=12, height=2,
                                command=self.toggle_relative,
                                bg="#333333", fg="#ffffff", font=("Arial", 10, "bold"))
        self.rel_btn.pack(pady=5)
        
        # Additional functions
        save_btn = tk.Button(func_frame, text="SAVE", width=12, height=2,
                            command=self.save_reading,
                            bg="#333333", fg="#ffffff", font=("Arial", 10))
        save_btn.pack(pady=5)
        
        # Light button for display backlight
        self.light_btn = tk.Button(func_frame, text="LIGHT", width=12, height=2,
                                  command=self.toggle_light,
                                  bg="#333333", fg="#ffffff", font=("Arial", 10))
        self.light_btn.pack(pady=5)
        
        self.update_unit()
        
    def set_mode(self, mode):
        self.measurement_mode.set(mode)
        self.reset_minmax()
        self.update_unit()
        
    def set_range(self, range_val):
        self.current_range.set(range_val)
        self.reset_minmax()
        
    def toggle_hold(self):
        self.hold_active.set(not self.hold_active.get())
        if self.hold_active.get():
            self.hold_btn.configure(bg="#ff0000")
            self.hold_indicator.config(text="HOLD")
            self.held_value = self.current_value
        else:
            self.hold_btn.configure(bg="#333333")
            self.hold_indicator.config(text="")
            
    def toggle_minmax(self):
        self.minmax_active.set(not self.minmax_active.get())
        if self.minmax_active.get():
            self.minmax_btn.configure(bg="#ff0000")
            self.minmax_indicator.config(text="MIN/MAX")
            self.minmax_frame.pack(fill=tk.X, pady=10)
            self.reset_minmax()
        else:
            self.minmax_btn.configure(bg="#333333")
            self.minmax_indicator.config(text="")
            self.minmax_frame.pack_forget()
            
    def toggle_relative(self):
        self.relative_active.set(not self.relative_active.get())
        if self.relative_active.get():
            self.rel_btn.configure(bg="#ff0000")
            self.rel_indicator.config(text="REL")
            self.relative_value = self.current_value
        else:
            self.rel_btn.configure(bg="#333333")
            self.rel_indicator.config(text="")
            
    def set_zero(self):
        self.zero_offset = self.current_value
        
    def reset_minmax(self):
        self.min_value = float('inf')
        self.max_value = float('-inf')
        self.min_label.config(text="MIN: ---")
        self.max_label.config(text="MAX: ---")
        
    def save_reading(self):
        # Placeholder for save functionality
        print(f"Saved reading: {self.current_value}")
        
    def toggle_light(self):
        # Toggle display backlight effect
        current_bg = self.display_label.cget("bg")
        if current_bg == "#000000":
            self.display_label.configure(bg="#111111")
            self.light_btn.configure(bg="#ff0000")
        else:
            self.display_label.configure(bg="#000000")
            self.light_btn.configure(bg="#333333")
            
    def update_unit(self):
        mode = self.measurement_mode.get()
        if "Voltage" in mode:
            self.unit_label.config(text="V")
        elif "Current" in mode:
            self.unit_label.config(text="A")
        elif "Resistance" in mode:
            self.unit_label.config(text="Ω")
        elif "Continuity" in mode:
            self.unit_label.config(text="Ω")
        elif "Diode" in mode:
            self.unit_label.config(text="V")
        elif "Capacitance" in mode:
            self.unit_label.config(text="F")
        elif "Frequency" in mode:
            self.unit_label.config(text="Hz")
        elif "Temperature" in mode:
            self.unit_label.config(text="°C")
        else:
            self.unit_label.config(text="")
            
    def simulate_readings(self):
        while self.running:
            mode = self.measurement_mode.get()
            
            # Generate simulated reading based on mode
            if "DC Voltage" in mode:
                base_value = random.uniform(1.2, 4.8)
                noise = random.uniform(-0.01, 0.01)
                value = base_value + noise
            elif "AC Voltage" in mode:
                base_value = random.uniform(110, 125)
                noise = random.uniform(-0.5, 0.5)
                value = base_value + noise
            elif "DC Current" in mode:
                base_value = random.uniform(0.1, 2.5)
                noise = random.uniform(-0.001, 0.001)
                value = base_value + noise
            elif "AC Current" in mode:
                base_value = random.uniform(0.5, 3.2)
                noise = random.uniform(-0.01, 0.01)
                value = base_value + noise
            elif "Resistance" in mode:
                base_value = random.uniform(100, 10000)
                noise = random.uniform(-1, 1)
                value = base_value + noise
            elif "Continuity" in mode:
                # Simulate continuity test
                if random.random() < 0.8:  # 80% chance of continuity
                    value = random.uniform(0.5, 50)
                else:
                    value = float('inf')  # Open circuit
            elif "Diode" in mode:
                base_value = random.uniform(0.5, 0.8)
                noise = random.uniform(-0.01, 0.01)
                value = base_value + noise
            elif "Capacitance" in mode:
                base_value = random.uniform(10, 1000)  # µF
                noise = random.uniform(-0.5, 0.5)
                value = base_value + noise
            elif "Frequency" in mode:
                base_value = random.uniform(45, 65)  # Hz
                noise = random.uniform(-0.1, 0.1)
                value = base_value + noise
            elif "Temperature" in mode:
                base_value = random.uniform(20, 30)  # °C
                noise = random.uniform(-0.1, 0.1)
                value = base_value + noise
            else:
                value = 0.0
                
            # Apply zero offset
            value -= self.zero_offset
            
            # Apply relative mode
            if self.relative_active.get():
                value -= self.relative_value
            
            # Update current value
            self.current_value = value
            
            # Update min/max
            if self.minmax_active.get():
                if value != float('inf'):  # Skip infinity values
                    if value < self.min_value:
                        self.min_value = value
                    if value > self.max_value:
                        self.max_value = value
                        
            # Update display
            if not self.hold_active.get():
                self.root.after(0, self.update_display, value)
                
            time.sleep(0.3)  # Update rate
            
    def update_display(self, value):
        # Format display value based on mode
        mode = self.measurement_mode.get()
        
        if value == float('inf'):
            display_text = "OL"
            unit_text = self.unit_label.cget("text")
        else:
            display_text, unit_text = self.format_value(value, mode)
            
        # Update display
        self.display_label.config(text=display_text)
        if unit_text != self.unit_label.cget("text"):
            self.unit_label.config(text=unit_text)
            
        # Update min/max display if active
        if self.minmax_active.get():
            if self.min_value != float('inf'):
                min_text, min_unit = self.format_value(self.min_value, mode)
                self.min_label.config(text=f"MIN: {min_text}")
            if self.max_value != float('-inf'):
                max_text, max_unit = self.format_value(self.max_value, mode)
                self.max_label.config(text=f"MAX: {max_text}")
                
    def format_value(self, value, mode):
        """Format value for display with appropriate units"""
        if value == float('inf'):
            return "OL", ""
            
        if "DC Voltage" in mode:
            if abs(value) < 1:
                return f"{value*1000:.1f}", "mV"
            else:
                return f"{value:.3f}", "V"
        elif "AC Voltage" in mode:
            return f"{value:.2f}", "V"
        elif "DC Current" in mode:
            if abs(value) < 1:
                return f"{value*1000:.1f}", "mA"
            else:
                return f"{value:.3f}", "A"
        elif "AC Current" in mode:
            return f"{value:.3f}", "A"
        elif "Resistance" in mode:
            if value < 1000:
                return f"{value:.1f}", "Ω"
            elif value < 1000000:
                return f"{value/1000:.1f}", "kΩ"
            else:
                return f"{value/1000000:.2f}", "MΩ"
        elif "Continuity" in mode:
            if value < 50:
                return f"{value:.1f}", "Ω"
            else:
                return "OL", "Ω"
        elif "Diode" in mode:
            return f"{value:.3f}", "V"
        elif "Capacitance" in mode:
            if value < 1:
                return f"{value*1000000:.0f}", "nF"
            else:
                return f"{value:.1f}", "µF"
        elif "Frequency" in mode:
            if value < 1000:
                return f"{value:.1f}", "Hz"
            else:
                return f"{value/1000:.2f}", "kHz"
        elif "Temperature" in mode:
            return f"{value:.1f}", "°C"
        else:
            return f"{value:.3f}", ""
            
    def on_closing(self):
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = DigitalMultimeter(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
