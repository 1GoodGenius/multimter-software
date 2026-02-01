import time
import statistics
from collections import deque
from typing import List, Optional, Tuple
from enum import Enum

class ReadingStatus(Enum):
    VALID = "valid"
    FLOATING = "floating"
    UNSTABLE = "unstable"
    NO_CONNECTION = "no_connection"

class FloatingInputDetector:
    def __init__(self, window_size: int = 10, max_variance: float = 0.5, 
                 min_stable_count: int = 5, floating_threshold: float = 2.0):
        """
        Initialize floating input detector.
        
        Args:
            window_size: Number of recent readings to analyze
            max_variance: Maximum allowed variance for stable readings
            min_stable_count: Minimum stable readings before considering valid
            floating_threshold: Threshold for detecting floating inputs (voltage)
        """
        self.window_size = window_size
        self.max_variance = max_variance
        self.min_stable_count = min_stable_count
        self.floating_threshold = floating_threshold
        
        self.reading_buffer = deque(maxlen=window_size)
        self.stable_count = 0
        self.last_stable_value = None
        self.detection_enabled = True
        
    def add_reading(self, value: float) -> ReadingStatus:
        """Add a new reading and determine its status"""
        if not self.detection_enabled:
            return ReadingStatus.VALID
            
        self.reading_buffer.append(value)
        
        if len(self.reading_buffer) < 3:
            return ReadingStatus.UNSTABLE
            
        # Check for floating input characteristics
        if self._is_floating_input():
            self.stable_count = 0
            return ReadingStatus.FLOATING
            
        # Check stability
        if self._is_stable():
            self.stable_count += 1
            if self.stable_count >= self.min_stable_count:
                self.last_stable_value = statistics.mean(self.reading_buffer)
                return ReadingStatus.VALID
            else:
                return ReadingStatus.UNSTABLE
        else:
            self.stable_count = 0
            return ReadingStatus.UNSTABLE
            
    def _is_floating_input(self) -> bool:
        """Detect if readings indicate floating input"""
        recent_readings = list(self.reading_buffer)
        
        # Check for high variance (random fluctuations)
        variance = statistics.variance(recent_readings) if len(recent_readings) > 1 else 0
        if variance > self.floating_threshold:
            return True
            
        # Check for readings near zero with high fluctuation
        near_zero_count = sum(1 for r in recent_readings if abs(r) < 0.1)
        if near_zero_count > len(recent_readings) * 0.7 and variance > 0.1:
            return True
            
        # Check for oscillating pattern
        if len(recent_readings) >= 4:
            sign_changes = sum(1 for i in range(1, len(recent_readings)) 
                             if recent_readings[i] * recent_readings[i-1] < 0)
            if sign_changes >= len(recent_readings) * 0.4:
                return True
                
        return False
        
    def _is_stable(self) -> bool:
        """Check if recent readings are stable"""
        if len(self.reading_buffer) < self.min_stable_count:
            return False
            
        recent_readings = list(self.reading_buffer)[-self.min_stable_count:]
        variance = statistics.variance(recent_readings)
        return variance <= self.max_variance
        
    def get_stable_reading(self) -> Optional[float]:
        """Get the last stable reading value"""
        return self.last_stable_value
        
    def reset(self):
        """Reset the detector state"""
        self.reading_buffer.clear()
        self.stable_count = 0
        self.last_stable_value = None
        
    def enable_detection(self, enabled: bool):
        """Enable or disable floating input detection"""
        self.detection_enabled = enabled
        
    def get_statistics(self) -> dict:
        """Get current statistics about readings"""
        if not self.reading_buffer:
            return {"count": 0, "mean": 0, "variance": 0, "status": "no_data"}
            
        readings = list(self.reading_buffer)
        return {
            "count": len(readings),
            "mean": statistics.mean(readings),
            "variance": statistics.variance(readings),
            "min": min(readings),
            "max": max(readings),
            "stable_count": self.stable_count,
            "last_stable": self.last_stable_value
        }

class MultimeterReadingProcessor:
    def __init__(self):
        self.detector = FloatingInputDetector()
        self.reading_history = deque(maxlen=100)
        self.connection_status = True
        
    def process_reading(self, raw_value: str) -> Tuple[Optional[float], ReadingStatus, str]:
        """
        Process a raw multimeter reading.
        
        Args:
            raw_value: Raw string reading from multimeter
            
        Returns:
            Tuple of (processed_value, status, display_message)
        """
        try:
            # Parse raw value
            if not raw_value or raw_value.strip() == "":
                return None, ReadingStatus.NO_CONNECTION, "No connection"
                
            # Extract numeric value
            numeric_value = self._parse_numeric_value(raw_value)
            if numeric_value is None:
                return None, ReadingStatus.NO_CONNECTION, "Invalid reading format"
                
            # Add to history
            self.reading_history.append(numeric_value)
            
            # Check for floating input
            status = self.detector.add_reading(numeric_value)
            
            # Generate appropriate message
            display_message = self._generate_display_message(numeric_value, status)
            
            return numeric_value, status, display_message
            
        except Exception as e:
            return None, ReadingStatus.NO_CONNECTION, f"Error: {str(e)}"
            
    def _parse_numeric_value(self, raw_value: str) -> Optional[float]:
        """Extract numeric value from raw multimeter reading"""
        import re
        
        # Remove common units and extract number
        cleaned = re.sub(r'[VvAaΩkMmµ]', '', raw_value.strip())
        cleaned = re.sub(r'[^\d.-]', '', cleaned)
        
        try:
            return float(cleaned)
        except ValueError:
            return None
            
    def _generate_display_message(self, value: float, status: ReadingStatus) -> str:
        """Generate appropriate display message based on reading status"""
        if status == ReadingStatus.FLOATING:
            return "⚠️ Floating input - connect probes"
        elif status == ReadingStatus.UNSTABLE:
            return f"🔄 Stabilizing... {value:.3f}"
        elif status == ReadingStatus.VALID:
            return f"✓ {value:.3f}"
        elif status == ReadingStatus.NO_CONNECTION:
            return "❌ No connection"
        else:
            return f"{value:.3f}"
            
    def get_current_reading(self) -> dict:
        """Get current reading information"""
        stats = self.detector.get_statistics()
        return {
            "connection_status": self.connection_status,
            "statistics": stats,
            "history_count": len(self.reading_history)
        }
        
    def reset_processor(self):
        """Reset the reading processor"""
        self.detector.reset()
        self.reading_history.clear()