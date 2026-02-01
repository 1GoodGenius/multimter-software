import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ImageProcessingConfig:
    """Configuration for image preprocessing parameters"""
    adaptive_threshold_block_size: int = 11
    adaptive_threshold_c: int = 2
    median_blur_kernel: int = 3
    gaussian_blur_kernel: Tuple[int, int] = (5, 5)
    gaussian_blur_sigma: int = 0
    apply_gaussian_blur: bool = True
    apply_morphology: bool = True
    morph_kernel_size: int = 3
    morph_operation: int = cv2.MORPH_CLOSE


class ImageProcessor:
    """Handles image preprocessing for OCR operations"""
    
    def __init__(self, config: Optional[ImageProcessingConfig] = None):
        self.config = config or ImageProcessingConfig()
        
    def load_image(self, image_path: str) -> np.ndarray:
        """Load image from file path"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        return img
        
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale"""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
    def apply_gaussian_blur(self, image: np.ndarray) -> np.ndarray:
        """Apply Gaussian blur to reduce noise"""
        if self.config.apply_gaussian_blur:
            return cv2.GaussianBlur(
                image, 
                self.config.gaussian_blur_kernel, 
                self.config.gaussian_blur_sigma
            )
        return image

# (rest copied)
