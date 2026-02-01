import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import time
import csv
from datetime import datetime
import json
import random
from collections import deque

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

# (file continues unchanged; full copy placed in new location)
