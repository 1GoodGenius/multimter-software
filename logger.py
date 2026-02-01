from pc_software.desktop.logger import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.logger", run_name="__main__")


logger = logging.getLogger(__name__)

class DataLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.is_logging = False
        self.data_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 100
    
    def start_logging(self, filename: Optional[str] = None) -> bool:
        """Start logging data to file"""
        if self.is_logging:
            logger.warning("Logging already in progress")
            return False
        
        try:
            if filename:
                log_file = self.log_dir / filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = self.log_dir / f"measurement_log_{timestamp}.csv"
            
            self.current_log_file = log_file
            self.is_logging = True
            self.data_buffer.clear()
            
            # Create CSV file with headers
            with open(log_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'voltage', 'current', 'resistance', 'notes'])
            
            logger.info(f"Started logging to {log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting logging: {e}")
            return False
    
    def stop_logging(self) -> bool:
        """Stop logging and save data"""
        if not self.is_logging:
            logger.warning("No logging in progress")
            return False
        
        try:
            # Write any remaining buffer data
            if self.data_buffer:
                self._write_buffer()
            
            self.is_logging = False
            logger.info(f"Stopped logging. Data saved to {self.current_log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping logging: {e}")
            return False
    
    def log_data(self, data: Dict[str, Any]) -> bool:
        """Log measurement data"""
        if not self.is_logging:
            return False
        
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'voltage': data.get('voltage', '0V'),
                'current': data.get('current', '0A'),
                'resistance': data.get('resistance', '0Ω'),
                'notes': data.get('notes', '')
            }
            
            self.data_buffer.append(log_entry)
            
            # Write buffer if it's full
            if len(self.data_buffer) >= self.max_buffer_size:
                self._write_buffer()
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging data: {e}")
            return False
    
    def _write_buffer(self):
        """Write buffer to file"""
        if not self.current_log_file or not self.data_buffer:
            return
        
        try:
            with open(self.current_log_file, 'a', newline='') as file:
                writer = csv.writer(file)
                for entry in self.data_buffer:
                    writer.writerow([
                        entry['timestamp'],
                        entry['voltage'],
                        entry['current'],
                        entry['resistance'],
                        entry['notes']
                    ])
            
            self.data_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error writing buffer: {e}")
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """Get list of existing log files"""
        log_files = []
        try:
            for file_path in self.log_dir.glob("*.csv"):
                stat = file_path.stat()
                log_files.append({
                    'filename': file_path.name,
                    'filepath': str(file_path),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # Sort by modified date (newest first)
            log_files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting log files: {e}")
        
        return log_files
    
    def load_log_file(self, filepath: str) -> Optional[List[Dict[str, Any]]]:
        """Load data from log file"""
        try:
            data = []
            with open(filepath, 'r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append({
                        'timestamp': row.get('timestamp', ''),
                        'voltage': row.get('voltage', '0V'),
                        'current': row.get('current', '0A'),
                        'resistance': row.get('resistance', '0Ω'),
                        'notes': row.get('notes', '')
                    })
            return data
            
        except Exception as e:
            logger.error(f"Error loading log file {filepath}: {e}")
            return None
    
    def export_to_json(self, csv_filepath: str, json_filepath: Optional[str] = None) -> bool:
        """Export CSV log file to JSON format"""
        try:
            data = self.load_log_file(csv_filepath)
            if not data:
                return False
            
            if not json_filepath:
                json_filepath = csv_filepath.replace('.csv', '.json')
            
            with open(json_filepath, 'w') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {csv_filepath} to {json_filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def delete_log_file(self, filepath: str) -> bool:
        """Delete a log file"""
        try:
            os.remove(filepath)
            logger.info(f"Deleted log file: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting log file: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current logging status"""
        return {
            'is_logging': self.is_logging,
            'current_file': str(self.current_log_file) if self.current_log_file else None,
            'buffer_size': len(self.data_buffer),
            'total_log_files': len(list(self.log_dir.glob("*.csv")))
        }