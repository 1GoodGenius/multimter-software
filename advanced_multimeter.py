#!/usr/bin/env python3
"""
Advanced Digital Multimeter GUI with Graphing and Data Logging
Includes real-time graphing, data export, and advanced measurement features.
"""

from pc_software.desktop.advanced_multimeter import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.advanced_multimeter", run_name="__main__")
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import math
import random
import time
import json
import csv
from datetime import datetime
from threading import Thread, Lock
from collections import deque
import re

class AdvancedMultimeter:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Digital Multimeter - Professional Edition")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Data protection
        self.data_lock = Lock()
        
        # Measurement modes with detailed configurations
        self.modes = {
            'ACV': {
                'name': 'AC Voltage', 
                'unit': 'V', 
                'range': ['600mV', '6V', '60V', '600V'],
                'color': '#00ff00',
                'resolution': ['0.1mV', '1mV', '10mV', '100mV'],
                'accuracy': '±(0.5%+2d)'
            },
            'DCV': {
                'name': 'DC Voltage', 
                'unit': 'V', 
                'range': ['600mV', '6V', '60V', '600V'],
                'color': '#00ff00',
                'resolution': ['0.1mV', '1mV', '10mV', '100mV'],
                'accuracy': '±(0.3%+1d)'
            },
            'DCA': {
                'name': 'DC Current', 
                'unit': 'A', 
                'range': ['600μA', '6000μA', '60mA', '600mA', '10A'],
                'color': '#00ff00',
                'resolution': ['0.1μA', '1μA', '10μA', '100μA', '1mA'],
                'accuracy': '±(0.5%+2d)'
            },
            'ACA': {
                'name': 'AC Current', 
                'unit': 'A', 
                'range': ['600μA', '6000μA', '60mA', '600mA', '10A'],
                'color': '#00ff00',
                'resolution': ['0.1μA', '1μA', '10μA', '100μA', '1mA'],
                'accuracy': '±(1.0%+3d)'
            },
            'Hz': {
                'name': 'Frequency', 
                'unit': 'Hz', 
                'range': ['100Hz', '1kHz', '10kHz', '100kHz', '1MHz'],
                'color': '#ffff00',
                'resolution': ['0.01Hz', '0.1Hz', '1Hz', '10Hz', '100Hz'],
                'accuracy': '±(0.01%+1d)'
            },
            'Ω': {
                'name': 'Resistance', 
                'unit': 'Ω', 
                'range': ['600Ω', '6kΩ', '60kΩ', '600kΩ', '6MΩ', '60MΩ'],
                'color': '#ffff00',
                'resolution': ['0.1Ω', '1Ω', '10Ω', '100Ω', '1kΩ', '10kΩ'],
                'accuracy': '±(0.5%+2d)'
            },
            'CAP': {
                'name': 'Capacitance', 
                'unit': 'F', 
                'range': ['10nF', '100nF', '1μF', '10μF', '100μF', '1mF'],
                'color': '#ffff00',
                'resolution': ['0.01nF', '0.1nF', '1nF', '10nF', '100nF', '1μF'],
                'accuracy': '±(3.0%+5d)'
            },
            'TEMP': {
                'name': 'Temperature', 
                'unit': '°C', 
                'range': ['-50°C', '200°C', '500°C', '1000°C'],
                'color': '#ff9900',
                'resolution': ['0.1°C', '1°C', '1°C', '1°C'],
                'accuracy': '±(1.0%+2°C)'
            },
            'DIODE': {
                'name': 'Diode Test', 
                'unit': 'V', 
                'range': ['2V'],
                'color': '#00ffff',
                'resolution': ['1mV'],
                'accuracy': '±(0.5%+2d)'
            },
            'CONT': {
                'name': 'Continuity', 
                'unit': 'Ω', 
                'range': ['600Ω'],
                'color': '#00ffff',
                'resolution': ['0.1Ω'],
                'accuracy': '±(0.5%+2d)'
            }
        }
        
        # State variables
        self.current_mode = 'DCV'
        self.current_range_index = 1
        self.current_value = 0.0
        self.measuring = False
        self.power_on = False
        self.auto_range = True
        self.hold_enabled = False
        self.hold_value = None
        self.max_min_enabled = False
        self.relative_enabled = False
        self.relative_zero = 0.0
        self.recording = False
        self.data_log = []
        
        # Threading
        self.simulation_thread = None
        self.graph_update_thread = None
        
        # Data storage
        self.value_history = deque(maxlen=1000)
        self.time_history = deque(maxlen=1000)
        self.max_values = deque(maxlen=100)
        self.min_values = deque(maxlen=100)
        
        # Setup UI
        self.setup_ui()
        self.bind_events()
        
        # Start update loops
        self.update_graphs()
        
    def setup_ui(self):
        # Create main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel (controls and display)
        left_frame = tk.Frame(main_paned, bg='#1a1a1a')
        main_paned.add(left_frame, weight=1)
        
        # Right panel (graphs)
        right_frame = tk.Frame(main_paned, bg='#1a1a1a')
        main_paned.add(right_frame, weight=2)
        
        # Setup individual panels
        self.setup_left_panel(left_frame)
        self.setup_right_panel(right_frame)
        
    def setup_left_panel(self, parent):
        # Control panel
        self.setup_control_panel(parent)
        
        # Display panel
        self.setup_display_panel(parent)
        
        # Mode selection
        self.setup_mode_panel(parent)
        
        # Range selection
        self.setup_range_panel(parent)
        
        # Status and info panel
        self.setup_status_panel(parent)
        
    def setup_right_panel(self, parent):
        # Graph controls
        self.setup_graph_controls(parent)
        
        # Graph display
        self.setup_graph_display(parent)
        
        # Data logging controls
        self.setup_logging_panel(parent)
        
    def setup_control_panel(self, parent):
        control_frame = tk.Frame(parent, bg='#2a2a2a', height=60)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        control_frame.pack_propagate(False)
        
        # Power button
        self.power_btn = tk.Button(
            control_frame,
            text="POWER",
            command=self.toggle_power,
            bg='#333333',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=10,
            height=2,
            relief=tk.RAISED,
            bd=3
        )
        self.power_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Auto Range button
        self.auto_range_btn = tk.Button(
            control_frame,
            text="AUTO",
            command=self.toggle_auto_range,
            bg='#00ff00',
            fg='black',
            font=('Arial', 10, 'bold'),
            width=8,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.auto_range_btn.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Hold button
        self.hold_btn = tk.Button(
            control_frame,
            text="HOLD",
            command=self.toggle_hold,
            bg='#333333',
            fg='white',
            font=('Arial', 10),
            width=8,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.hold_btn.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Max/Min button
        self.maxmin_btn = tk.Button(
            control_frame,
            text="MAX/MIN",
            command=self.toggle_maxmin,
            bg='#333333',
            fg='white',
            font=('Arial', 10),
            width=10,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.maxmin_btn.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Relative button
        self.rel_btn = tk.Button(
            control_frame,
            text="REL",
            command=self.toggle_relative,
            bg='#333333',
            fg='white',
            font=('Arial', 10),
            width=6,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.rel_btn.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Record button
        self.record_btn = tk.Button(
            control_frame,
            text="REC",
            command=self.toggle_recording,
            bg='#333333',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=6,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        self.record_btn.pack(side=tk.LEFT, padx=5, pady=10)
        
    def setup_display_panel(self, parent):
        display_frame = tk.Frame(parent, bg='#000000', height=200)
        display_frame.pack(fill=tk.X, pady=(0, 10))
        display_frame.pack_propagate(False)
        
        # Main display
        self.display_var = tk.StringVar(value="0.000")
        self.display_label = tk.Label(
            display_frame,
            textvariable=self.display_var,
            font=('Courier', 72, 'bold'),
            bg='#000000',
            fg='#00ff00',
            anchor='e',
            padx=20,
            pady=10
        )
        self.display_label.pack(fill=tk.BOTH, expand=True)
        
        # Secondary display (bar graph)
        self.bar_frame = tk.Frame(display_frame, bg='#000000', height=30)
        self.bar_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.bar_canvas = tk.Canvas(
            self.bar_frame,
            bg='#111111',
            height=20,
            highlightthickness=0
        )
        self.bar_canvas.pack(fill=tk.X)
        
        # Unit and mode display
        info_frame = tk.Frame(display_frame, bg='#000000')
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.unit_var = tk.StringVar(value="V")
        self.unit_label = tk.Label(
            info_frame,
            textvariable=self.unit_var,
            font=('Arial', 24, 'bold'),
            bg='#000000',
            fg='#00ff00'
        )
        self.unit_label.pack(side=tk.LEFT)
        
        self.mode_var = tk.StringVar(value="DC Voltage")
        self.mode_label = tk.Label(
            info_frame,
            textvariable=self.mode_var,
            font=('Arial', 14),
            bg='#000000',
            fg='#888888'
        )
        self.mode_label.pack(side=tk.RIGHT)
        
    def setup_mode_panel(self, parent):
        mode_frame = tk.Frame(parent, bg='#2a2a2a')
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            mode_frame,
            text="Measurement Mode:",
            font=('Arial', 12, 'bold'),
            bg='#2a2a2a',
            fg='white'
        ).pack(anchor='w', padx=10, pady=5)
        
        # Mode buttons in grid
        modes_grid = [
            ['ACV', 'DCV', 'Hz'],
            ['ACA', 'DCA', 'Ω'],
            ['CAP', 'TEMP', 'DIODE'],
            ['CONT']
        ]
        
        self.mode_buttons = {}
        
        for i, row in enumerate(modes_grid):
            row_frame = tk.Frame(mode_frame, bg='#2a2a2a')
            row_frame.pack(fill=tk.X, pady=2)
            
            for mode in row:
                if mode in self.modes:
                    btn = tk.Button(
                        row_frame,
                        text=f"{mode}\n{self.modes[mode]['name']}",
                        command=lambda m=mode: self.set_mode(m),
                        bg='#444444',
                        fg='white',
                        font=('Arial', 9, 'bold'),
                        width=12,
                        height=2,
                        relief=tk.RAISED,
                        bd=2
                    )
                    btn.pack(side=tk.LEFT, padx=5, pady=2)
                    self.mode_buttons[mode] = btn
                    
        self.update_mode_buttons()
        
    def setup_range_panel(self, parent):
        range_frame = tk.Frame(parent, bg='#2a2a2a')
        range_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            range_frame,
            text="Range:",
            font=('Arial', 12, 'bold'),
            bg='#2a2a2a',
            fg='white'
        ).pack(anchor='w', padx=10, pady=5)
        
        # Range selection
        self.range_var = tk.StringVar()
        self.range_combo = ttk.Combobox(
            range_frame,
            textvariable=self.range_var,
            state='readonly',
            font=('Arial', 10),
            width=20
        )
        self.range_combo.pack(padx=10, pady=5)
        self.range_combo.bind('<<ComboboxSelected>>', self.on_range_change)
        
        # Update range options based on current mode
        self.update_range_options()
        
    def setup_status_panel(self, parent):
        status_frame = tk.Frame(parent, bg='#2a2a2a', height=80)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        # Status information
        info_frame = tk.Frame(status_frame, bg='#2a2a2a')
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Status label
        self.status_var = tk.StringVar(value="Power Off")
        tk.Label(
            info_frame,
            textvariable=self.status_var,
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='#888888'
        ).grid(row=0, column=0, sticky='w')
        
        # Accuracy info
        self.accuracy_var = tk.StringVar(value="")
        tk.Label(
            info_frame,
            textvariable=self.accuracy_var,
            font=('Arial', 9),
            bg='#2a2a2a',
            fg='#888888'
        ).grid(row=1, column=0, sticky='w')
        
        # Max/Min display
        self.maxmin_display_var = tk.StringVar(value="")
        tk.Label(
            info_frame,
            textvariable=self.maxmin_display_var,
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='#ffff00'
        ).grid(row=0, column=1, sticky='e', padx=20)
        
        # Time display
        self.time_var = tk.StringVar(value="")
        tk.Label(
            info_frame,
            textvariable=self.time_var,
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='#888888'
        ).grid(row=1, column=1, sticky='e', padx=20)
        
        info_frame.columnconfigure(1, weight=1)
        
        # Update time
        self.update_time()
        
    def setup_graph_controls(self, parent):
        graph_control_frame = tk.Frame(parent, bg='#2a2a2a', height=40)
        graph_control_frame.pack(fill=tk.X, pady=(0, 5))
        graph_control_frame.pack_propagate(False)
        
        # Graph type selection
        tk.Label(
            graph_control_frame,
            text="Graph Type:",
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        self.graph_type_var = tk.StringVar(value="Line")
        graph_types = ["Line", "Bar", "Histogram", "Min/Max"]
        self.graph_type_combo = ttk.Combobox(
            graph_control_frame,
            textvariable=self.graph_type_var,
            values=graph_types,
            state='readonly',
            width=15
        )
        self.graph_type_combo.pack(side=tk.LEFT, padx=5)
        
        # Time range
        tk.Label(
            graph_control_frame,
            text="Time Range:",
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='white'
        ).pack(side=tk.LEFT, padx=10)
        
        self.time_range_var = tk.StringVar(value="60s")
        time_ranges = ["30s", "60s", "120s", "300s", "All"]
        self.time_range_combo = ttk.Combobox(
            graph_control_frame,
            textvariable=self.time_range_var,
            values=time_ranges,
            state='readonly',
            width=10
        )
        self.time_range_combo.pack(side=tk.LEFT, padx=5)
        
        # Clear graph button
        tk.Button(
            graph_control_frame,
            text="Clear Graph",
            command=self.clear_graph,
            bg='#ff6666',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.RIGHT, padx=5)
        
    def setup_graph_display(self, parent):
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=80, facecolor='#1a1a1a')
        self.ax = self.fig.add_subplot(111, facecolor='#000000')
        
        # Configure plot appearance
        self.ax.set_xlabel('Time (s)', color='white', fontsize=10)
        self.ax.set_ylabel('Value', color='white', fontsize=10)
        self.ax.set_title('Real-time Measurement', color='white', fontsize=12)
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.grid(True, alpha=0.3, color='gray')
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def setup_logging_panel(self, parent):
        logging_frame = tk.Frame(parent, bg='#2a2a2a', height=60)
        logging_frame.pack(fill=tk.X, pady=5)
        logging_frame.pack_propagate(False)
        
        # Export buttons
        tk.Button(
            logging_frame,
            text="Export CSV",
            command=self.export_csv,
            bg='#0099ff',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        tk.Button(
            logging_frame,
            text="Export JSON",
            command=self.export_json,
            bg='#0099ff',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        # Recording indicator
        self.recording_indicator = tk.Label(
            logging_frame,
            text="●",
            font=('Arial', 20),
            bg='#2a2a2a',
            fg='#333333'
        )
        self.recording_indicator.pack(side=tk.RIGHT, padx=10)
        
        # Data points counter
        self.data_count_var = tk.StringVar(value="0 points")
        tk.Label(
            logging_frame,
            textvariable=self.data_count_var,
            font=('Arial', 10),
            bg='#2a2a2a',
            fg='white'
        ).pack(side=tk.RIGHT, padx=5)
        
    def bind_events(self):
        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self.toggle_power())
        self.root.bind('<h>', lambda e: self.toggle_hold())
        self.root.bind('<a>', lambda e: self.toggle_auto_range())
        self.root.bind('<r>', lambda e: self.toggle_recording())
        self.root.bind('<m>', lambda e: self.toggle_maxmin())
        self.root.bind('<z>', lambda e: self.toggle_relative())
        
        # Mode selection with number keys
        for i, mode in enumerate(list(self.modes.keys())[:9]):
            self.root.bind(str(i+1), lambda e, m=mode: self.set_mode(m))
            
        # Rotary encoder simulation
        self.root.bind('<Left>', lambda e: self.previous_mode())
        self.root.bind('<Right>', lambda e: self.next_mode())
        self.root.bind('<Up>', lambda e: self.next_range())
        self.root.bind('<Down>', lambda e: self.previous_range())
        
        # Export shortcuts
        self.root.bind('<Control-e>', lambda e: self.export_csv())
        self.root.bind('<Control-j>', lambda e: self.export_json())
        
    def toggle_power(self):
        self.power_on = not self.power_on
        if self.power_on:
            self.power_btn.configure(bg='#00ff00', text='ON')
            self.status_var.set("Measuring")
            self.measuring = True
            self.start_simulation()
        else:
            self.power_btn.configure(bg='#333333', text='POWER')
            self.status_var.set("Power Off")
            self.measuring = False
            self.stop_simulation()
            self.display_var.set("0.000")
            
    def toggle_auto_range(self):
        self.auto_range = not self.auto_range
        if self.auto_range:
            self.auto_range_btn.configure(bg='#00ff00', fg='black')
            self.range_combo.configure(state='disabled')
        else:
            self.auto_range_btn.configure(bg='#333333', fg='white')
            self.range_combo.configure(state='readonly')
            
    def toggle_hold(self):
        self.hold_enabled = not self.hold_enabled
        if self.hold_enabled:
            self.hold_value = self.current_value
            self.hold_btn.configure(bg='#ff9900', fg='white')
        else:
            self.hold_value = None
            self.hold_btn.configure(bg='#333333', fg='white')
            
    def toggle_maxmin(self):
        self.max_min_enabled = not self.max_min_enabled
        if self.max_min_enabled:
            self.maxmin_btn.configure(bg='#0099ff', fg='white')
            self.max_values.clear()
            self.min_values.clear()
        else:
            self.maxmin_btn.configure(bg='#333333', fg='white')
            self.maxmin_display_var.set("")
            
    def toggle_relative(self):
        self.relative_enabled = not self.relative_enabled
        if self.relative_enabled:
            self.relative_zero = self.current_value
            self.rel_btn.configure(bg='#ff00ff', fg='white')
        else:
            self.relative_enabled = False
            self.rel_btn.configure(bg='#333333', fg='white')
            
    def toggle_recording(self):
        self.recording = not self.recording
        if self.recording:
            self.record_btn.configure(bg='#ff0000', fg='white')
            self.recording_indicator.configure(fg='#ff0000')
        else:
            self.record_btn.configure(bg='#333333', fg='white')
            self.recording_indicator.configure(fg='#333333')
            
    def set_mode(self, mode):
        if mode in self.modes:
            self.current_mode = mode
            self.mode_var.set(self.modes[mode]['name'])
            self.update_mode_buttons()
            self.update_range_options()
            self.update_accuracy_display()
            
            # Update display color
            color = self.modes[mode]['color']
            self.display_label.configure(fg=color)
            self.unit_label.configure(fg=color)
            
    def update_mode_buttons(self):
        for mode, btn in self.mode_buttons.items():
            if mode == self.current_mode:
                btn.configure(bg='#00ff00', fg='black')
            else:
                btn.configure(bg='#444444', fg='white')
                
    def update_range_options(self):
        ranges = self.modes[self.current_mode]['range']
        self.range_combo['values'] = ranges
        
        if self.auto_range:
            self.range_var.set("AUTO")
        else:
            if self.current_range_index < len(ranges):
                self.range_var.set(ranges[self.current_range_index])
                
    def on_range_change(self, event=None):
        if not self.auto_range:
            ranges = self.modes[self.current_mode]['range']
            try:
                self.current_range_index = ranges.index(self.range_var.get())
            except ValueError:
                pass
                
    def next_range(self):
        if not self.auto_range:
            ranges = self.modes[self.current_mode]['range']
            self.current_range_index = (self.current_range_index + 1) % len(ranges)
            self.range_var.set(ranges[self.current_range_index])
            
    def previous_range(self):
        if not self.auto_range:
            ranges = self.modes[self.current_mode]['range']
            self.current_range_index = (self.current_range_index - 1) % len(ranges)
            self.range_var.set(ranges[self.current_range_index])
            
    def previous_mode(self):
        modes = list(self.modes.keys())
        current_index = modes.index(self.current_mode)
        previous_index = (current_index - 1) % len(modes)
        self.set_mode(modes[previous_index])
        
    def next_mode(self):
        modes = list(self.modes.keys())
        current_index = modes.index(self.current_mode)
        next_index = (current_index + 1) % len(modes)
        self.set_mode(modes[next_index])
        
    def update_accuracy_display(self):
        accuracy = self.modes[self.current_mode]['accuracy']
        self.accuracy_var.set(f"Accuracy: {accuracy}")
        
    def update_time(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)
        
    def clear_graph(self):
        with self.data_lock:
            self.value_history.clear()
            self.time_history.clear()
        self.update_graph()
        
    def start_simulation(self):
        if self.simulation_thread is None or not self.simulation_thread.is_alive():
            self.simulation_thread = Thread(target=self.simulate_measurement, daemon=True)
            self.simulation_thread.start()
            
    def stop_simulation(self):
        self.measuring = False
        
    def simulate_measurement(self):
        """Generate realistic measurement values"""
        start_time = time.time()
        
        while self.measuring:
            if not self.hold_enabled:
                # Generate realistic values based on mode
                if self.current_mode == 'DCV':
                    # DC Voltage with realistic fluctuations
                    base_value = random.uniform(0.5, 12.5)
                    noise = random.gauss(0, 0.02)
                    self.current_value = max(0, base_value + noise)
                    
                elif self.current_mode == 'ACV':
                    # AC Voltage (RMS equivalent)
                    base_value = random.uniform(10, 240)
                    noise = random.gauss(0, 0.5)
                    self.current_value = max(0, base_value + noise)
                    
                elif self.current_mode == 'DCA':
                    # DC Current
                    base_value = random.uniform(0.001, 2.0)
                    noise = random.gauss(0, 0.005)
                    self.current_value = max(0, base_value + noise)
                    
                elif self.current_mode == 'ACA':
                    # AC Current
                    base_value = random.uniform(0.01, 5.0)
                    noise = random.gauss(0, 0.02)
                    self.current_value = max(0, base_value + noise)
                    
                elif self.current_mode == 'Hz':
                    # Frequency measurement
                    if random.random() > 0.8:
                        # Mains frequency
                        self.current_value = random.choice([50, 60]) + random.gauss(0, 0.1)
                    else:
                        # Other frequencies
                        self.current_value = random.uniform(1, 10000)
                        
                elif self.current_mode == 'Ω':
                    # Resistance with wide range
                    rand = random.random()
                    if rand < 0.2:
                        self.current_value = random.uniform(1, 1000)
                    elif rand < 0.4:
                        self.current_value = random.uniform(1000, 100000)
                    elif rand < 0.6:
                        self.current_value = random.uniform(100000, 1000000)
                    elif rand < 0.8:
                        self.current_value = random.uniform(1000000, 10000000)
                    else:
                        self.current_value = random.uniform(10000000, 100000000)
                        
                elif self.current_mode == 'CAP':
                    # Capacitance
                    rand = random.random()
                    if rand < 0.3:
                        self.current_value = random.uniform(1e-9, 1e-6)  # nF to μF
                    elif rand < 0.6:
                        self.current_value = random.uniform(1e-6, 1e-3)  # μF to mF
                    else:
                        self.current_value = random.uniform(1e-3, 1e-2)  # mF
                        
                elif self.current_mode == 'TEMP':
                    # Temperature
                    self.current_value = random.uniform(-20, 100) + random.gauss(0, 0.5)
                    
                elif self.current_mode == 'DIODE':
                    # Diode test
                    if random.random() > 0.3:
                        self.current_value = random.uniform(0.5, 0.8)
                    else:
                        self.current_value = float('inf')
                        
                elif self.current_mode == 'CONT':
                    # Continuity test
                    if random.random() > 0.3:
                        self.current_value = random.uniform(0, 50)
                    else:
                        self.current_value = float('inf')
                        
                # Apply relative measurement
                if self.relative_enabled:
                    self.current_value -= self.relative_zero
                    
                # Auto-range if enabled
                if self.auto_range:
                    self.auto_select_range()
                    
            # Store data with timestamp
            with self.data_lock:
                current_time = time.time() - start_time
                self.time_history.append(current_time)
                self.value_history.append(self.current_value)
                
                # Max/Min tracking
                if self.max_min_enabled:
                    self.max_values.append(self.current_value)
                    self.min_values.append(self.current_value)
                    
                # Recording
                if self.recording:
                    self.data_log.append({
                        'time': datetime.now().isoformat(),
                        'value': self.current_value,
                        'mode': self.current_mode,
                        'unit': self.modes[self.current_mode]['unit']
                    })
                    
            # Update display
            self.root.after(0, self.update_display)
            
            # Sampling rate
            time.sleep(0.1)  # 10Hz update rate
            
    def auto_select_range(self):
        """Automatically select the best range based on current value"""
        if self.current_value == float('inf'):
            return
            
        ranges = self.modes[self.current_mode]['range']
        
        # Parse range values to numeric
        range_values = []
        for r in ranges:
            # Extract numeric value from range string
            match = re.search(r'([\d.]+)', r)
            if match:
                value = float(match.group(1))
                # Handle multipliers
                if 'm' in r.lower() and 'V' in r:
                    value /= 1000
                elif 'k' in r.lower():
                    value *= 1000
                elif 'M' in r.lower():
                    value *= 1000000
                elif 'μ' in r.lower():
                    value /= 1000000
                elif 'n' in r.lower():
                    value /= 1000000000
                range_values.append(value)
            else:
                range_values.append(float('inf'))
                
        # Find best range (value should be less than range max)
        best_range = 0
        for i, range_val in enumerate(range_values):
            if abs(self.current_value) <= range_val:
                best_range = i
                break
                
        self.current_range_index = best_range
        
    def update_display(self):
        """Update the main display with current value"""
        display_value = self.hold_value if self.hold_enabled else self.current_value
        
        # Format based on mode
        if self.current_mode in ['CONT', 'DIODE']:
            if display_value == float('inf') or display_value > 1000:
                self.display_var.set("OL")  # Overload
                self.unit_var.set("")
            else:
                if self.current_mode == 'CONT':
                    if display_value < 50:
                        self.display_var.set("CONT")
                        self.display_label.configure(fg='#ffffff')
                    else:
                        self.display_var.set(f"{display_value:.1f}")
                        self.display_label.configure(fg=self.modes[self.current_mode]['color'])
                else:  # DIODE
                    self.display_var.set(f"{display_value:.3f}")
                self.unit_var.set(self.modes[self.current_mode]['unit'])
                
        elif self.current_mode == 'Ω':
            if display_value >= 1000000:
                self.display_var.set(f"{display_value/1000000:.3f}")
                self.unit_var.set("MΩ")
            elif display_value >= 1000:
                self.display_var.set(f"{display_value/1000:.3f}")
                self.unit_var.set("kΩ")
            else:
                self.display_var.set(f"{display_value:.1f}")
                self.unit_var.set("Ω")
                
        elif self.current_mode == 'CAP':
            if display_value >= 0.001:
                self.display_var.set(f"{display_value:.3f}")
                self.unit_var.set("mF")
            elif display_value >= 0.000001:
                self.display_var.set(f"{display_value*1000:.3f}")
                self.unit_var.set("μF")
            else:
                self.display_var.set(f"{display_value*1000000:.0f}")
                self.unit_var.set("nF")
                
        elif self.current_mode == 'Hz':
            if display_value >= 1000:
                self.display_var.set(f"{display_value/1000:.3f}")
                self.unit_var.set("kHz")
            else:
                self.display_var.set(f"{display_value:.1f}")
                self.unit_var.set("Hz")
                
        else:  # Voltage and Current
            if abs(display_value) >= 1000:
                self.display_var.set(f"{display_value/1000:.3f}")
                unit_char = self.modes[self.current_mode]['unit']
                self.unit_var.set(f"k{unit_char}")
            elif abs(display_value) < 1 and abs(display_value) > 0:
                self.display_var.set(f"{display_value*1000:.3f}")
                unit_char = self.modes[self.current_mode]['unit']
                self.unit_var.set(f"m{unit_char}")
            else:
                self.display_var.set(f"{display_value:.3f}")
                self.unit_var.set(self.modes[self.current_mode]['unit'])
                
        # Update bar graph
        self.update_bar_graph(display_value)
        
        # Update max/min display
        if self.max_min_enabled and self.max_values and self.min_values:
            max_val = max(self.max_values)
            min_val = min(self.min_values)
            self.maxmin_display_var.set(f"MAX: {max_val:.3f}  MIN: {min_val:.3f}")
            
        # Update data count
        self.data_count_var.set(f"{len(self.data_log)} points")
        
    def update_bar_graph(self, value):
        """Update the small bar graph display"""
        if value == float('inf'):
            return
            
        # Get current range for scaling
        ranges = self.modes[self.current_mode]['range']
        current_range = ranges[self.current_range_index]
        
        # Extract max value from range
        match = re.search(r'([\d.]+)', current_range)
        if match:
            max_val = float(match.group(1))
            # Handle multipliers
            if 'm' in current_range and 'V' in current_range:
                max_val /= 1000
            elif 'k' in current_range:
                max_val *= 1000
            elif 'M' in current_range:
                max_val *= 1000000
        else:
            max_val = 600  # Default
            
        # Scale value to bar width
        if abs(value) <= max_val:
            bar_width = int((abs(value) / max_val) * (self.bar_frame.winfo_width() - 40))
        else:
            bar_width = self.bar_frame.winfo_width() - 40
            
        # Clear and redraw bar
        self.bar_canvas.delete("all")
        if bar_width > 0:
            self.bar_canvas.create_rectangle(
                0, 0, bar_width, 20,
                fill=self.modes[self.current_mode]['color'],
                outline=""
            )
            
    def update_graph(self):
        """Update the main graph display"""
        if not self.value_history:
            return
            
        with self.data_lock:
            times = list(self.time_history)
            values = list(self.value_history)
            
        if not times:
            return
            
        self.ax.clear()
        
        # Get time range
        time_range = self.time_range_var.get()
        if time_range == "All":
            time_cutoff = 0
        else:
            time_cutoff = times[-1] - float(time_range.replace('s', ''))
            
        # Filter data based on time range
        filtered_times = []
        filtered_values = []
        for t, v in zip(times, values):
            if t >= time_cutoff:
                filtered_times.append(t)
                filtered_values.append(v)
                
        if not filtered_times:
            return
            
        # Plot based on selected graph type
        graph_type = self.graph_type_var.get()
        
        if graph_type == "Line":
            self.ax.plot(filtered_times, filtered_values, 
                        color=self.modes[self.current_mode]['color'], 
                        linewidth=2)
        elif graph_type == "Bar":
            if len(filtered_times) < 100:  # Limit bar chart for performance
                self.ax.bar(range(len(filtered_values)), filtered_values,
                           color=self.modes[self.current_mode]['color'])
                self.ax.set_xlabel('Sample Number')
            else:
                self.ax.plot(filtered_times, filtered_values,
                           color=self.modes[self.current_mode]['color'])
        elif graph_type == "Histogram":
            self.ax.hist(filtered_values, bins=30, 
                        color=self.modes[self.current_mode]['color'], 
                        alpha=0.7)
            self.ax.set_xlabel('Value Distribution')
        elif graph_type == "Min/Max" and self.max_min_enabled:
            if self.max_values and self.min_values:
                max_times = times[-len(self.max_values):]
                min_times = times[-len(self.min_values):]
                self.ax.plot(max_times, list(self.max_values), 
                           color='red', label='Maximum', linewidth=2)
                self.ax.plot(min_times, list(self.min_values), 
                           color='blue', label='Minimum', linewidth=2)
                self.ax.legend()
                
        # Set labels and title
        if graph_type != "Histogram":
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel(f'{self.modes[self.current_mode]["name"]} ({self.modes[self.current_mode]["unit"]})')
        
        self.ax.set_title(f'{self.modes[self.current_mode]["name"]} - Real-time Measurement')
        self.ax.grid(True, alpha=0.3, color='gray')
        
        # Style
        self.ax.set_facecolor('#000000')
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values():
            spine.set_color('white')
            
        self.canvas.draw()
        
    def update_graphs(self):
        """Periodic graph update"""
        if self.measuring:
            self.update_graph()
        self.root.after(500, self.update_graphs)  # Update every 500ms
        
    def export_csv(self):
        """Export data to CSV file"""
        if not self.data_log:
            messagebox.showwarning("No Data", "No data to export. Start recording first.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = ['time', 'value', 'mode', 'unit']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.data_log)
                messagebox.showinfo("Export Successful", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
                
    def export_json(self):
        """Export data to JSON file"""
        if not self.data_log:
            messagebox.showwarning("No Data", "No data to export. Start recording first.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as jsonfile:
                    json.dump(self.data_log, jsonfile, indent=2)
                messagebox.showinfo("Export Successful", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

def main():
    root = tk.Tk()
    app = AdvancedMultimeter(root)
    root.mainloop()

if __name__ == "__main__":
    main()