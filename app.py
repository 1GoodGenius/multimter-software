from pc_software.desktop.app import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.app", run_name="__main__")

import random
import math
import time
from datetime import datetime
import json

app = Flask(__name__)

class MultimeterSimulator:
    """Simulates digital multimeter measurements for demonstration"""
    
    def __init__(self):
        self.base_values = {
            'voltage': 12.5,
            'current': 2.3,
            'resistance': 1000,
            'capacitance': 100,
            'continuity': False,
            'temperature': 25.0,
            'frequency': 50.0,
            'duty_cycle': 50.0
        }
        self.time_offset = 0
        
    def get_measurements(self):
        """Generate realistic measurement values with noise"""
        t = time.time() + self.time_offset
        
        measurements = {
            'voltage': self.base_values['voltage'] + 
                       math.sin(t * 0.5) * 0.5 + 
                       random.gauss(0, 0.05),
            'current': self.base_values['current'] + 
                       math.cos(t * 0.8) * 0.2 + 
                       random.gauss(0, 0.02),
            'resistance': self.base_values['resistance'] + 
                          math.sin(t * 0.3) * 50 + 
                          random.gauss(0, 5),
            'capacitance': self.base_values['capacitance'] + 
                           math.cos(t * 0.6) * 10 + 
                           random.gauss(0, 1),
            'continuity': random.random() > 0.9,
            'temperature': self.base_values['temperature'] + 
                          math.sin(t * 0.2) * 2 + 
                          random.gauss(0, 0.2),
            'frequency': self.base_values['frequency'] + 
                        math.cos(t * 0.4) * 2 + 
                        random.gauss(0, 0.2),
            'duty_cycle': self.base_values['duty_cycle'] + 
                          math.sin(t * 0.7) * 10 + 
                          random.gauss(0, 1)
        }
        
        # Calculate power values
        voltage = measurements['voltage']
        current = measurements['current']
        
        measurements.update({
            'active_power': abs(voltage * current),
            'reactive_power': abs(voltage * current * 0.3),
            'apparent_power': abs(voltage * current * 1.1),
            'power_factor': min(1.0, abs(voltage * current) / (abs(voltage * current) * 1.1)),
            'efficiency': 85 + random.random() * 10
        })
        
        return measurements

# Initialize simulator
multimeter = MultimeterSimulator()

@app.route('/')
def index():
    """Serve the main multimeter interface"""
    return render_template('index.html')

@app.route('/api/measurements')
def get_measurements():
    """API endpoint to get current measurements"""
    measurements = multimeter.get_measurements()
    
    return jsonify({
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'measurements': measurements
    })

@app.route('/api/connect', methods=['POST'])
def connect():
    """Simulate multimeter connection"""
    return jsonify({
        'status': 'success',
        'connected': True,
        'message': 'Multimeter connected successfully'
    })

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Simulate multimeter disconnection"""
    return jsonify({
        'status': 'success',
        'connected': False,
        'message': 'Multimeter disconnected'
    })

@app.route('/api/calibrate', methods=['POST'])
def calibrate():
    """Simulate calibration process"""
    return jsonify({
        'status': 'success',
        'message': 'Calibration completed'
    })

@app.route('/api/range/<measurement>', methods=['POST'])
def set_range(measurement):
    """Set measurement range"""
    data = request.get_json()
    range_value = data.get('range', 'auto')
    
    return jsonify({
        'status': 'success',
        'measurement': measurement,
        'range': range_value,
        'message': f'{measurement} range set to {range_value}'
    })

@app.route('/api/zero', methods=['POST'])
def zero_meter():
    """Zero/relative measurement"""
    multimeter.time_offset = random.random() * 100  # Simulate zero adjustment
    
    return jsonify({
        'status': 'success',
        'message': 'Meter zeroed successfully'
    })

@app.route('/api/data/save', methods=['POST'])
def save_data():
    """Save measurement data"""
    data = request.get_json()
    
    # In a real implementation, this would save to database or file
    saved_data = {
        'timestamp': datetime.now().isoformat(),
        'data': data,
        'saved': True
    }
    
    return jsonify({
        'status': 'success',
        'message': 'Data saved successfully',
        'saved_data': saved_data
    })

@app.route('/api/data/export', methods=['POST'])
def export_data():
    """Export measurement data as CSV"""
    data = request.get_json()
    
    # Generate CSV data
    csv_lines = ['Timestamp,Measurement,Value,Unit']
    
    if 'measurements' in data:
        timestamp = datetime.now().isoformat()
        for measurement, value in data['measurements'].items():
            unit = {
                'voltage': 'V',
                'current': 'A',
                'resistance': 'Ω',
                'capacitance': 'μF',
                'temperature': '°C',
                'frequency': 'Hz',
                'duty_cycle': '%'
            }.get(measurement, '')
            
            csv_lines.append(f"{timestamp},{measurement},{value},{unit}")
    
    csv_data = '\n'.join(csv_lines)
    
    return jsonify({
        'status': 'success',
        'csv_data': csv_data,
        'filename': f"multimeter_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'digital_multimeter'
    })

if __name__ == '__main__':
    print("Digital Multimeter Web Interface")
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    # Run in debug mode for development
    app.run(debug=True, host='0.0.0.0', port=5000)