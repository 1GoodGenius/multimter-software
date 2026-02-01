import cv2
import numpy as np
import pytesseract
import re
from PIL import Image
import os

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

    # (rest of file copied verbatim into new location)
