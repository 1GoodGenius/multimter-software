from pc_software.desktop.multimeter_analyzer import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.multimeter_analyzer", run_name="__main__")


class MultimeterAnalyzer:
    def __init__(self):
        self.specifications = {}
        
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR accuracy"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.medianBlur(thresh, 3)
        
        return denoised
    
    def extract_text(self, image_path):
        """Extract text from image using OCR"""
        processed_img = self.preprocess_image(image_path)
        
        # Configure tesseract for better results on digital displays
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.VAΩHz%µmACDCFKMW'
        
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        return text
    
    def extract_specifications(self, text):
        """Extract multimeter specifications from OCR text"""
        specs = {}
        
        # Extract voltage ranges
        voltage_pattern = r'(\d+\.?\d*)\s*[VmV]'
        voltages = re.findall(voltage_pattern, text)
        if voltages:
            specs['voltage_ranges'] = [float(v) for v in voltages]
        
        # Extract current ranges
        current_pattern = r'(\d+\.?\d*)\s*[Aaµm]'
        currents = re.findall(current_pattern, text)
        if currents:
            specs['current_ranges'] = [float(c) for c in currents]
        
        # Extract resistance ranges
        resistance_pattern = r'(\d+\.?\d*)\s*[ΩkM]'
        resistances = re.findall(resistance_pattern, text)
        if resistances:
            specs['resistance_ranges'] = [float(r) for r in resistances]
        
        # Extract frequency
        freq_pattern = r'(\d+\.?\d*)\s*Hz'
        frequencies = re.findall(freq_pattern, text)
        if frequencies:
            specs['frequency_ranges'] = [float(f) for f in frequencies]
        
        # Extract capacitance
        cap_pattern = r'(\d+\.?\d*)\s*[µnF]'
        capacitances = re.findall(cap_pattern, text)
        if capacitances:
            specs['capacitance_ranges'] = [float(c) for c in capacitances]
        
        # Look for AC/DC indicators
        if 'AC' in text.upper():
            specs['ac_measurement'] = True
        if 'DC' in text.upper():
            specs['dc_measurement'] = True
            
        # Look for auto range
        if 'AUTO' in text.upper() or 'AUTORANGE' in text.upper():
            specs['auto_range'] = True
            
        return specs
    
    def analyze_multimeter(self, image_path):
        """Analyze a multimeter image and return specifications"""
        try:
            text = self.extract_text(image_path)
            specs = self.extract_specifications(text)
            specs['raw_text'] = text
            return specs
        except Exception as e:
            return {'error': str(e)}
    
    def generate_product_description(self, specs):
        """Generate a product description based on extracted specifications"""
        if 'error' in specs:
            return f"Error analyzing image: {specs['error']}"
        
        description = "Digital Multimeter with the following specifications:\n\n"
        
        if specs.get('voltage_ranges'):
            description += f"• Voltage Measurement: {', '.join(map(str, specs['voltage_ranges']))}V\n"
        
        if specs.get('current_ranges'):
            description += f"• Current Measurement: {', '.join(map(str, specs['current_ranges']))}A\n"
        
        if specs.get('resistance_ranges'):
            description += f"• Resistance Measurement: {', '.join(map(str, specs['resistance_ranges']))}Ω\n"
        
        if specs.get('frequency_ranges'):
            description += f"• Frequency Measurement: {', '.join(map(str, specs['frequency_ranges']))}Hz\n"
        
        if specs.get('capacitance_ranges'):
            description += f"• Capacitance Measurement: {', '.join(map(str, specs['capacitance_ranges']))}F\n"
        
        if specs.get('ac_measurement'):
            description += "• AC Measurement Capability\n"
        
        if specs.get('dc_measurement'):
            description += "• DC Measurement Capability\n"
        
        if specs.get('auto_range'):
            description += "• Auto Range Function\n"
        
        return description

def main():
    """Main function to analyze multimeter images"""
    analyzer = MultimeterAnalyzer()
    
    # List of common image paths to check
    possible_paths = [
        "DSC_0032.JPG",
        "DSC_0033.JPG", 
        "DSC_0034.JPG",
        "DSC_0035.JPG",
        "*.JPG",
        "*.jpg"
    ]
    
    print("Digital Multimeter Specification Analyzer")
    print("=" * 50)
    
    found_images = []
    for pattern in possible_paths:
        if os.path.exists(pattern):
            found_images.append(pattern)
        elif "*" in pattern:
            import glob
            found_images.extend(glob.glob(pattern))
    
    if not found_images:
        print("No multimeter images found. Please ensure image files are in the current directory.")
        print("Looking for files like: DSC_0032.JPG, DSC_0033.JPG, etc.")
        return
    
    all_specs = {}
    
    for image_path in found_images:
        print(f"\nAnalyzing: {image_path}")
        print("-" * 30)
        
        specs = analyzer.analyze_multimeter(image_path)
        
        if 'error' not in specs:
            print(analyzer.generate_product_description(specs))
            print(f"Raw OCR Text:\n{specs['raw_text']}")
            all_specs[image_path] = specs
        else:
            print(f"Error: {specs['error']}")
    
    # Generate combined specifications if multiple images
    if len(all_specs) > 1:
        print(f"\n{'='*50}")
        print("COMBINED SPECIFICATIONS FROM ALL IMAGES")
        print("=" * 50)
        
        combined_specs = {}
        for specs in all_specs.values():
            for key, value in specs.items():
                if key != 'raw_text' and key not in combined_specs:
                    combined_specs[key] = value
                elif key != 'raw_text' and isinstance(value, list):
                    if key not in combined_specs:
                        combined_specs[key] = []
                    combined_specs[key].extend([v for v in value if v not in combined_specs[key]])
        
        print(analyzer.generate_product_description(combined_specs))

if __name__ == "__main__":
    main()