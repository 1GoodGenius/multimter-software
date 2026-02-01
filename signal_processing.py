from pc_software.desktop.signal_processing import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.signal_processing", run_name="__main__")

class SignalProcessor:
    def __init__(self, sample_rate: float = 1000.0):
        self.sample_rate = sample_rate
        self.processing_enabled = True
    
    def set_sample_rate(self, sample_rate: float):
        """Update sample rate for calculations"""
        self.sample_rate = sample_rate
        logger.info(f"Sample rate set to {sample_rate} Hz")
    
    def apply_filter(self, data: np.ndarray, filter_type: str = "lowpass", 
                    cutoff: float = 100.0, order: int = 4) -> np.ndarray:
        """Apply digital filter to data"""
        try:
            nyquist = self.sample_rate / 2
            normalized_cutoff = cutoff / nyquist
            
            if filter_type == "lowpass":
                b, a = scipy.signal.butter(order, normalized_cutoff, btype='low')
            elif filter_type == "highpass":
                b, a = scipy.signal.butter(order, normalized_cutoff, btype='high')
            elif filter_type == "bandpass":
                # For bandpass, cutoff should be [low, high]
                if isinstance(cutoff, list) and len(cutoff) == 2:
                    normalized_cutoff = [freq / nyquist for freq in cutoff]
                else:
                    raise ValueError("Bandpass requires cutoff as [low, high] list")
                b, a = scipy.signal.butter(order, normalized_cutoff, btype='band')
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
            
            filtered_data = scipy.signal.filtfilt(b, a, data)
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            return data
    
    def remove_dc_offset(self, data: np.ndarray) -> np.ndarray:
        """Remove DC offset from signal"""
        try:
            return data - np.mean(data)
        except Exception as e:
            logger.error(f"Error removing DC offset: {e}")
            return data
    
    def calculate_rms(self, data: np.ndarray) -> float:
        """Calculate RMS value of signal"""
        try:
            return np.sqrt(np.mean(np.square(data)))
        except Exception as e:
            logger.error(f"Error calculating RMS: {e}")
            return 0.0
    
    def calculate_peak_to_peak(self, data: np.ndarray) -> float:
        """Calculate peak-to-peak amplitude"""
        try:
            return np.max(data) - np.min(data)
        except Exception as e:
            logger.error(f"Error calculating peak-to-peak: {e}")
            return 0.0
    
    def calculate_frequency_spectrum(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate frequency spectrum using FFT"""
        try:
            n = len(data)
            if n == 0:
                return np.array([]), np.array([])
            
            # Apply window function to reduce spectral leakage
            windowed_data = data * scipy.signal.windows.hann(n)
            
            # Compute FFT
            fft_values = fft(windowed_data)
            frequencies = fftfreq(n, 1/self.sample_rate)
            
            # Return only positive frequencies
            positive_freq_idx = frequencies > 0
            frequencies = frequencies[positive_freq_idx]
            magnitude = np.abs(fft_values[positive_freq_idx])
            
            return frequencies, magnitude
            
        except Exception as e:
            logger.error(f"Error calculating frequency spectrum: {e}")
            return np.array([]), np.array([])
    
    def find_peaks(self, data: np.ndarray, height: Optional[float] = None, 
                  distance: Optional[int] = None) -> Dict[str, np.ndarray]:
        """Find peaks in signal"""
        try:
            peaks, properties = scipy.signal.find_peaks(
                data, 
                height=height, 
                distance=distance
            )
            
            return {
                'peaks': peaks,
                'peak_heights': properties.get('peak_heights', np.array([]))
            }
            
        except Exception as e:
            logger.error(f"Error finding peaks: {e}")
            return {'peaks': np.array([]), 'peak_heights': np.array([])}
    
    def calculate_thd(self, data: np.ndarray, fundamental_freq: float) -> Optional[float]:
        """Calculate Total Harmonic Distortion (THD)"""
        try:
            frequencies, magnitude = self.calculate_frequency_spectrum(data)
            
            if len(frequencies) == 0:
                return None
            
            # Find fundamental frequency peak
            fundamental_idx = np.argmin(np.abs(frequencies - fundamental_freq))
            fundamental_magnitude = magnitude[fundamental_idx]
            
            if fundamental_magnitude == 0:
                return None
            
            # Calculate harmonics (2nd to 10th)
            harmonic_power = 0.0
            for harmonic in range(2, 11):
                harmonic_freq = harmonic * fundamental_freq
                if harmonic_freq > frequencies[-1]:
                    break
                
                harmonic_idx = np.argmin(np.abs(frequencies - harmonic_freq))
                harmonic_magnitude = magnitude[harmonic_idx]
                harmonic_power += harmonic_magnitude ** 2
            
            # THD calculation
            thd = np.sqrt(harmonic_power) / fundamental_magnitude * 100
            return thd
            
        except Exception as e:
            logger.error(f"Error calculating THD: {e}")
            return None
    
    def calculate_snr(self, signal: np.ndarray, noise_start_idx: int, 
                     noise_end_idx: int) -> Optional[float]:
        """Calculate Signal-to-Noise Ratio (SNR) in dB"""
        try:
            # Extract noise region
            noise = signal[noise_start_idx:noise_end_idx]
            noise_power = np.mean(np.square(noise))
            
            # Calculate signal power (excluding noise region)
            signal_mask = np.ones(len(signal), dtype=bool)
            signal_mask[noise_start_idx:noise_end_idx] = False
            signal_data = signal[signal_mask]
            signal_power = np.mean(np.square(signal_data))
            
            if noise_power == 0:
                return float('inf')
            
            snr_db = 10 * np.log10(signal_power / noise_power)
            return snr_db
            
        except Exception as e:
            logger.error(f"Error calculating SNR: {e}")
            return None
    
    def apply_moving_average(self, data: np.ndarray, window_size: int = 5) -> np.ndarray:
        """Apply moving average filter"""
        try:
            if window_size <= 0:
                return data
            
            # Use convolution for moving average
            kernel = np.ones(window_size) / window_size
            return np.convolve(data, kernel, mode='same')
            
        except Exception as e:
            logger.error(f"Error applying moving average: {e}")
            return data
    
    def detect_zero_crossings(self, data: np.ndarray) -> np.ndarray:
        """Detect zero crossings in signal"""
        try:
            # Find zero crossings
            sign_changes = np.diff(np.signbit(data))
            zero_crossings = np.where(sign_changes)[0]
            
            return zero_crossings
            
        except Exception as e:
            logger.error(f"Error detecting zero crossings: {e}")
            return np.array([])
    
    def calculate_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """Calculate basic statistics for signal"""
        try:
            return {
                'mean': float(np.mean(data)),
                'std': float(np.std(data)),
                'min': float(np.min(data)),
                'max': float(np.max(data)),
                'rms': self.calculate_rms(data),
                'peak_to_peak': self.calculate_peak_to_peak(data),
                'length': len(data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def process_waveform(self, data: np.ndarray, filter_settings: Optional[Dict] = None) -> Dict[str, Any]:
        """Process complete waveform with comprehensive analysis"""
        try:
            if not self.processing_enabled or len(data) == 0:
                return {}
            
            processed_data = data.copy()
            
            # Apply filtering if requested
            if filter_settings:
                filter_type = filter_settings.get('type', 'lowpass')
                cutoff = filter_settings.get('cutoff', 100.0)
                order = filter_settings.get('order', 4)
                
                if filter_type != 'none':
                    processed_data = self.apply_filter(processed_data, filter_type, cutoff, order)
            
            # Remove DC offset
            processed_data = self.remove_dc_offset(processed_data)
            
            # Calculate comprehensive analysis
            stats = self.calculate_statistics(processed_data)
            frequencies, magnitude = self.calculate_frequency_spectrum(processed_data)
            peaks = self.find_peaks(processed_data)
            zero_crossings = self.detect_zero_crossings(processed_data)
            
            # Find dominant frequency
            if len(magnitude) > 0:
                dominant_freq_idx = np.argmax(magnitude)
                dominant_frequency = frequencies[dominant_freq_idx]
            else:
                dominant_frequency = 0.0
            
            result = {
                'processed_data': processed_data,
                'statistics': stats,
                'frequency_spectrum': {
                    'frequencies': frequencies,
                    'magnitude': magnitude
                },
                'peaks': peaks,
                'zero_crossings': zero_crossings,
                'dominant_frequency': dominant_frequency,
                'sample_rate': self.sample_rate
            }
            
            # Calculate THD if dominant frequency is significant
            if dominant_frequency > 0:
                thd = self.calculate_thd(processed_data, dominant_frequency)
                if thd is not None:
                    result['thd'] = thd
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing waveform: {e}")
            return {}
    
    def enable_processing(self, enabled: bool = True):
        """Enable or disable signal processing"""
        self.processing_enabled = enabled
        logger.info(f"Signal processing {'enabled' if enabled else 'disabled'}")
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        return {
            'enabled': self.processing_enabled,
            'sample_rate': self.sample_rate
        }