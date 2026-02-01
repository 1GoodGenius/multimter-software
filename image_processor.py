from pc_software.desktop.image_processor import *

if __name__ == "__main__":
    import runpy
    runpy.run_module("pc_software.desktop.image_processor", run_name="__main__")



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
        
    def apply_adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding for binarization"""
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            self.config.adaptive_threshold_block_size, 
            self.config.adaptive_threshold_c
        )
        
    def apply_median_blur(self, image: np.ndarray) -> np.ndarray:
        """Apply median blur for denoising"""
        return cv2.medianBlur(image, self.config.median_blur_kernel)
        
    def apply_morphology(self, image: np.ndarray) -> np.ndarray:
        """Apply morphological operations"""
        if self.config.apply_morphology:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT, 
                (self.config.morph_kernel_size, self.config.morph_kernel_size)
            )
            return cv2.morphologyEx(image, self.config.morph_operation, kernel)
        return image
        
    def preprocess(self, image_path: str) -> np.ndarray:
        """Complete preprocessing pipeline"""
        # Load and convert to grayscale
        img = self.load_image(image_path)
        gray = self.convert_to_grayscale(img)
        
        # Apply preprocessing steps
        blurred = self.apply_gaussian_blur(gray)
        thresh = self.apply_adaptive_threshold(blurred)
        denoised = self.apply_median_blur(thresh)
        final = self.apply_morphology(denoised)
        
        return final
        
    def get_processing_info(self) -> Dict[str, Any]:
        """Get current processing configuration"""
        return {
            'adaptive_threshold_block_size': self.config.adaptive_threshold_block_size,
            'adaptive_threshold_c': self.config.adaptive_threshold_c,
            'median_blur_kernel': self.config.median_blur_kernel,
            'gaussian_blur_kernel': self.config.gaussian_blur_kernel,
            'apply_gaussian_blur': self.config.apply_gaussian_blur,
            'apply_morphology': self.config.apply_morphology,
            'morph_operation': self.config.morph_operation
        }