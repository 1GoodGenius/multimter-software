// Digital Multimeter JavaScript

class DigitalMultimeter {
    constructor() {
        this.isConnected = false;
        this.measurementInterval = null;
        this.holdValue = false;
        this.minMaxMode = false;
        this.relativeMode = false;
        this.relativeValues = {};
        this.minValues = {};
        this.maxValues = {};
        this.previousValues = {};
        this.animationFrames = {};
        this.measurementHistory = {};
        this.maxHistoryLength = 10;
        
        this.initializeMeter();
        this.startAnimations();
        this.setupEventListeners();
    }

    initializeMeter() {
        this.updateConnectionStatus(false);
        this.updateAllDisplays();
        this.startPeriodicUpdates();
        this.showStatus('Multimeter initialized', 'info');
    }

    setupEventListeners() {
        // Range selectors
        document.getElementById('voltageRangeSelect').addEventListener('change', (e) => {
            this.updateRange('voltage', e.target.value);
        });
        
        document.getElementById('currentRangeSelect').addEventListener('change', (e) => {
            this.updateRange('current', e.target.value);
        });
        
        document.getElementById('resistanceRangeSelect').addEventListener('change', (e) => {
            this.updateRange('resistance', e.target.value);
        });

        // Measurement rate
        document.getElementById('measurementRate').addEventListener('change', (e) => {
            this.setMeasurementRate(e.target.value);
        });

        // Display mode
        document.getElementById('displayMode').addEventListener('change', (e) => {
            this.setDisplayMode(e.target.value);
        });

        // Touch support for mobile
        this.addTouchSupport();
    }

    addTouchSupport() {
        const displays = document.querySelectorAll('.meter-display');
        displays.forEach(display => {
            display.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.handleTouchStart(display);
            });
            
            display.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.handleTouchEnd(display);
            });
        });
    }

    handleTouchStart(display) {
        display.style.transform = 'scale(0.98)';
    }

    handleTouchEnd(display) {
        display.style.transform = '';
        // Could add additional touch actions here
    }

    startPeriodicUpdates() {
        // Update measurements every 200ms for responsive feel
        setInterval(() => {
            if (!this.holdValue) {
                this.updateMeasurements();
            }
        }, 200);

        // Update stability indicators every 500ms
        setInterval(() => {
            this.updateStabilityIndicators();
        }, 500);
    }

    updateMeasurements() {
        // Simulate realistic measurement values
        const measurements = this.generateMeasurements();
        
        this.updateDisplay('voltage', measurements.voltage, 'V');
        this.updateDisplay('current', measurements.current, 'A');
        this.updateDisplay('resistance', measurements.resistance, 'Ω');
        this.updateDisplay('capacitance', measurements.capacitance, 'μF');
        this.updateDisplay('continuity', measurements.continuity, '');
        this.updateDisplay('temperature', measurements.temperature, '°C');
        this.updateDisplay('frequency', measurements.frequency, 'Hz');
        this.updateDisplay('dutyCycle', measurements.dutyCycle, '%');
        
        this.updatePowerCalculations(measurements);
    }

    generateMeasurements() {
        // Generate realistic measurement values with some noise
        const baseValues = {
            voltage: 12.5 + Math.sin(Date.now() / 1000) * 0.5 + (Math.random() - 0.5) * 0.1,
            current: 2.3 + Math.cos(Date.now() / 800) * 0.2 + (Math.random() - 0.5) * 0.05,
            resistance: 1000 + Math.sin(Date.now() / 1200) * 50 + (Math.random() - 0.5) * 10,
            capacitance: 100 + Math.cos(Date.now() / 900) * 10 + (Math.random() - 0.5) * 2,
            continuity: Math.random() > 0.8 ? 'Closed' : 'Open',
            temperature: 25 + Math.sin(Date.now() / 2000) * 2 + (Math.random() - 0.5) * 0.5,
            frequency: 50 + Math.cos(Date.now() / 1100) * 2 + (Math.random() - 0.5) * 0.5,
            dutyCycle: 50 + Math.sin(Date.now() / 700) * 10 + (Math.random() - 0.5) * 2
        };

        // Apply relative mode if active
        Object.keys(baseValues).forEach(key => {
            if (this.relativeMode && this.relativeValues[key] !== undefined) {
                if (typeof baseValues[key] === 'number') {
                    baseValues[key] = baseValues[key] - this.relativeValues[key];
                }
            }
        });

        return baseValues;
    }

    updateDisplay(measurement, value, unit) {
        // Store history for stability calculation
        if (!this.measurementHistory[measurement]) {
            this.measurementHistory[measurement] = [];
        }
        
        this.measurementHistory[measurement].push(value);
        if (this.measurementHistory[measurement].length > this.maxHistoryLength) {
            this.measurementHistory[measurement].shift();
        }

        // Handle min/max mode
        if (this.minMaxMode) {
            this.updateMinMax(measurement, value);
        }

        const element = document.getElementById(`${measurement}Value`);
        if (element) {
            let displayValue = value;
            
            if (typeof value === 'number') {
                displayValue = value.toFixed(2);
                
                // Auto-scale units for large values
                if (unit === 'Ω' && value >= 1000) {
                    displayValue = (value / 1000).toFixed(2);
                    unit = 'kΩ';
                } else if (unit === 'Ω' && value >= 1000000) {
                    displayValue = (value / 1000000).toFixed(2);
                    unit = 'MΩ';
                } else if (unit === 'A' && value < 0.001) {
                    displayValue = (value * 1000).toFixed(2);
                    unit = 'mA';
                } else if (unit === 'A' && value < 1) {
                    displayValue = (value * 1000).toFixed(1);
                    unit = 'mA';
                } else if (unit === 'V' && value < 1) {
                    displayValue = (value * 1000).toFixed(1);
                    unit = 'mV';
                }
            }
            
            element.innerHTML = `${displayValue}<span class="meter-unit">${unit}</span>`;
            
            // Add animation for value changes
            element.style.animation = 'none';
            setTimeout(() => {
                element.style.animation = 'pulse 0.3s ease';
            }, 10);
        }
    }

    updateMinMax(measurement, value) {
        if (typeof value !== 'number') return;
        
        if (this.minValues[measurement] === undefined || value < this.minValues[measurement]) {
            this.minValues[measurement] = value;
        }
        
        if (this.maxValues[measurement] === undefined || value > this.maxValues[measurement]) {
            this.maxValues[measurement] = value;
        }
    }

    updateStabilityIndicators() {
        Object.keys(this.measurementHistory).forEach(measurement => {
            const history = this.measurementHistory[measurement];
            if (history.length < 3) return;
            
            // Calculate stability based on variance
            const recentValues = history.slice(-5);
            const mean = recentValues.reduce((a, b) => a + b, 0) / recentValues.length;
            
            if (typeof mean === 'number') {
                const variance = recentValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / recentValues.length;
                const stdDev = Math.sqrt(variance);
                const stability = Math.max(0, Math.min(100, 100 - (stdDev / Math.abs(mean)) * 100));
                
                this.updateStabilityBar(measurement, stability);
            }
        });
    }

    updateStabilityBar(measurement, stability) {
        const bar = document.getElementById(`${measurement}Stability`);
        const text = document.getElementById(`${measurement}StabilityText`);
        
        if (bar && text) {
            bar.style.width = `${stability}%`;
            text.textContent = `${Math.round(stability)}%`;
            
            // Change color based on stability level
            if (stability > 80) {
                bar.style.background = 'linear-gradient(90deg, #44ff44, #00aa00)';
            } else if (stability > 50) {
                bar.style.background = 'linear-gradient(90deg, #ffaa00, #ff8800)';
            } else {
                bar.style.background = 'linear-gradient(90deg, #ff4444, #cc0000)';
            }
        }
    }

    updatePowerCalculations(measurements) {
        const { voltage, current } = measurements;
        
        if (typeof voltage === 'number' && typeof current === 'number') {
            const activePower = Math.abs(voltage * current);
            const apparentPower = activePower * 1.1; // Simulate PF
            const reactivePower = Math.sqrt(Math.pow(apparentPower, 2) - Math.pow(activePower, 2));
            const powerFactor = activePower / apparentPower;
            const efficiency = Math.min(95, 85 + Math.random() * 10);
            
            this.updatePowerDisplay('activePower', activePower, 'W');
            this.updatePowerDisplay('reactivePower', reactivePower, 'VAR');
            this.updatePowerDisplay('apparentPower', apparentPower, 'VA');
            this.updateIndicatorDisplay('powerFactor', powerFactor, '');
            this.updateIndicatorDisplay('efficiency', efficiency, '%');
        }
    }

    updatePowerDisplay(elementId, value, unit) {
        const element = document.getElementById(elementId);
        if (element) {
            let displayValue = value.toFixed(2);
            if (unit === 'W' && value >= 1000) {
                displayValue = (value / 1000).toFixed(2);
                unit = 'kW';
            } else if (unit === 'VA' && value >= 1000) {
                displayValue = (value / 1000).toFixed(2);
                unit = 'kVA';
            }
            element.innerHTML = `${displayValue}<span class="power-unit">${unit}</span>`;
        }
    }

    updateIndicatorDisplay(elementId, value, suffix) {
        const element = document.getElementById(elementId);
        const bar = document.getElementById(`${elementId}Bar`);
        
        if (element) {
            const displayValue = elementId === 'efficiency' ? 
                `${Math.round(value)}${suffix}` : 
                value.toFixed(2);
            element.textContent = displayValue;
        }
        
        if (bar) {
            bar.style.width = `${value}%`;
        }
    }

    updateConnectionStatus(connected) {
        this.isConnected = connected;
        const indicator = document.getElementById('statusIndicator');
        const status = document.getElementById('connectionStatus');
        
        if (connected) {
            indicator.classList.add('connected');
            status.textContent = 'Connected';
            this.showStatus('Multimeter connected successfully', 'success');
        } else {
            indicator.classList.remove('connected');
            status.textContent = 'Disconnected';
            this.showStatus('Multimeter disconnected', 'warning');
        }
    }

    updateRange(measurement, range) {
        const rangeElement = document.getElementById(`${measurement}Range`);
        if (rangeElement) {
            rangeElement.textContent = range === 'auto' ? 'Auto Range' : range;
        }
        this.showStatus(`${measurement.charAt(0).toUpperCase() + measurement.slice(1)} range set to ${range}`, 'info');
    }

    setMeasurementRate(rate) {
        const rateMap = {
            'fast': 100,
            'normal': 200,
            'slow': 1000
        };
        
        // Simulate rate change
        this.showStatus(`Measurement rate set to ${rate}`, 'info');
    }

    setDisplayMode(mode) {
        // Reset modes
        this.minMaxMode = false;
        this.relativeMode = false;
        
        switch(mode) {
            case 'minmax':
                this.minMaxMode = true;
                this.resetMinMax();
                this.showStatus('Min/Max mode activated', 'info');
                break;
            case 'relative':
                this.relativeMode = true;
                this.setRelativeValues();
                this.showStatus('Relative mode activated', 'info');
                break;
            case 'value':
                this.showStatus('Value only mode', 'info');
                break;
            case 'trend':
                this.showStatus('Trend mode activated', 'info');
                break;
        }
    }

    resetMinMax() {
        this.minValues = {};
        this.maxValues = {};
    }

    setRelativeValues() {
        // Set current values as reference for relative mode
        Object.keys(this.measurementHistory).forEach(measurement => {
            const history = this.measurementHistory[measurement];
            if (history.length > 0) {
                const recent = history.slice(-3);
                const mean = recent.reduce((a, b) => a + b, 0) / recent.length;
                if (typeof mean === 'number') {
                    this.relativeValues[measurement] = mean;
                }
            }
        });
    }

    showStatus(message, type = 'info') {
        const statusElement = document.getElementById('statusMessage');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status-message ${type}`;
            statusElement.style.display = 'block';
            
            setTimeout(() => {
                statusElement.style.display = 'none';
            }, 3000);
        }
    }

    updateAllDisplays() {
        const displays = [
            'voltage', 'current', 'resistance', 'capacitance', 
            'continuity', 'temperature', 'frequency', 'dutyCycle'
        ];
        
        displays.forEach(display => {
            const element = document.getElementById(`${display}Value`);
            if (element) {
                element.innerHTML = `0.00<span class="meter-unit">${this.getUnit(display)}</span>`;
            }
        });
    }

    getUnit(measurement) {
        const units = {
            voltage: 'V',
            current: 'A',
            resistance: 'Ω',
            capacitance: 'μF',
            continuity: '',
            temperature: '°C',
            frequency: 'Hz',
            dutyCycle: '%'
        };
        return units[measurement] || '';
    }

    startAnimations() {
        // Animate ultrasonic transducers
        this.animateTransducers();
        
        // Add CSS animation keyframes if not already present
        this.addPulseAnimation();
    }

    animateTransducers() {
        const transducers = document.querySelectorAll('.transducer-img');
        
        transducers.forEach((transducer, index) => {
            // Create wave animation
            this.animateTransducerWaves(transducer, index);
        });
    }

    animateTransducerWaves(transducer, index) {
        const waves = transducer.querySelectorAll('path');
        const phase = index * (Math.PI * 2 / 3); // Phase offset for each transducer
        
        setInterval(() => {
            const time = Date.now() / 1000;
            waves.forEach((wave, waveIndex) => {
                const opacity = 0.3 + 0.4 * Math.sin(time * 2 + phase + waveIndex * 0.5);
                wave.style.opacity = opacity;
            });
        }, 50);
    }

    addPulseAnimation() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.02); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
}

// Global control functions
function zeroMeter() {
    meter.setRelativeValues();
    meter.setDisplayMode('relative');
}

function holdValue() {
    meter.holdValue = !meter.holdValue;
    meter.showStatus(meter.holdValue ? 'Value held' : 'Value tracking resumed', 'info');
}

function toggleMinmax() {
    meter.setDisplayMode('minmax');
}

function calibrate() {
    meter.showStatus('Calibration started...', 'info');
    setTimeout(() => {
        meter.showStatus('Calibration completed successfully', 'success');
    }, 2000);
}

function saveData() {
    const data = {
        timestamp: new Date().toISOString(),
        measurements: meter.measurementHistory,
        minValues: meter.minValues,
        maxValues: meter.maxValues
    };
    
    localStorage.setItem('multimeter_data', JSON.stringify(data));
    meter.showStatus('Data saved to local storage', 'success');
}

function exportData() {
    const data = {
        timestamp: new Date().toISOString(),
        measurements: meter.measurementHistory,
        minValues: meter.minValues,
        maxValues: meter.maxValues
    };
    
    const csv = this.convertToCSV(data);
    this.downloadCSV(csv, `multimeter_data_${new Date().toISOString().slice(0, 10)}.csv`);
    meter.showStatus('Data exported as CSV', 'success');
}

function convertToCSV(data) {
    const headers = ['Timestamp', 'Measurement', 'Value', 'Min', 'Max'];
    const rows = [headers.join(',')];
    
    Object.keys(data.measurements).forEach(measurement => {
        const values = data.measurements[measurement];
        values.forEach((value, index) => {
            const timestamp = new Date(Date.now() - (values.length - index) * 200).toISOString();
            const min = data.minValues[measurement] || '';
            const max = data.maxValues[measurement] || '';
            rows.push([timestamp, measurement, value, min, max].join(','));
        });
    });
    
    return rows.join('\n');
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Initialize the multimeter when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.meter = new DigitalMultimeter();
    
    // Simulate connection after a delay
    setTimeout(() => {
        meter.updateConnectionStatus(true);
    }, 1500);
});

// Handle visibility changes for performance
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pause animations when tab is not visible
        console.log('Multimeter paused - tab not visible');
    } else {
        // Resume animations when tab becomes visible
        console.log('Multimeter resumed - tab visible');
    }
});

// Handle window resize for responsive adjustments
window.addEventListener('resize', () => {
    // Adjust layout for mobile/desktop
    if (window.innerWidth < 768) {
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
});