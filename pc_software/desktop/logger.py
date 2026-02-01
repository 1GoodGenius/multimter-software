import logging
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class DataLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.is_logging = False
        self.data_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 100

    # (rest copied)
