import os
import re

def analyze_multimeter_from_filenames():
    """Analyze multimeter specifications based on file naming patterns"""
    
    print("Digital Multimeter Specification Analyzer")
    print("=" * 50)
    print("Looking for multimeter image files...")
    
    # Common multimeter image patterns
    image_patterns = [
        "DSC_0032.JPG", "DSC_0033.JPG", "DSC_0034.JPG", "DSC_0035.JPG",
        "*.JPG", "*.jpg", "*.PNG", "*.png"
    ]
    
    found_files = []
    for pattern in image_patterns:
        if os.path.exists(pattern):
            found_files.append(pattern)
        elif "*" in pattern:
            import glob
            found_files.extend(glob.glob(pattern))

# (rest copied)
