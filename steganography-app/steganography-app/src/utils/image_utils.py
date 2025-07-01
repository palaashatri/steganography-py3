import numpy as np
from PIL import Image
import cv2
from typing import Optional, Tuple

def load_image(image_path):
    from PIL import Image
    return Image.open(image_path)

def save_image(image, save_path):
    image.save(save_path)

def convert_image_to_rgba(image):
    return image.convert("RGBA")

def resize_image(image, size):
    return image.resize(size)

def get_image_size(image):
    return image.size

def image_to_bytes(image):
    from io import BytesIO
    byte_io = BytesIO()
    image.save(byte_io, format='PNG')
    return byte_io.getvalue()

def bytes_to_image(image_bytes):
    from PIL import Image
    from io import BytesIO
    byte_io = BytesIO(image_bytes)
    return Image.open(byte_io)

class ImageProcessor:
    """Image processing utilities for steganography"""
    
    def __init__(self):
        pass
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image and convert to numpy array"""
        try:
            pil_image = Image.open(image_path)
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            return np.array(pil_image)
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def save_image(self, image_array: np.ndarray, output_path: str) -> bool:
        """Save numpy array as image"""
        try:
            # Ensure values are in valid range
            image_array = np.clip(image_array, 0, 255).astype(np.uint8)
            pil_image = Image.fromarray(image_array)
            pil_image.save(output_path)
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            return False
    
    def validate_image(self, image_path: str) -> bool:
        """Validate if image can be loaded and is suitable for steganography"""
        try:
            image = self.load_image(image_path)
            if image is None:
                return False
            
            # Check minimum size requirements
            height, width = image.shape[:2]
            if height < 10 or width < 10:
                return False
                
            return True
        except:
            return False
    
    def get_image_capacity(self, image_path: str, algorithm: str = "LSB") -> int:
        """Calculate maximum data capacity for the image"""
        try:
            image = self.load_image(image_path)
            if image is None:
                return 0
            
            height, width, channels = image.shape
            
            if algorithm == "LSB":
                # 1 bit per pixel per channel
                return (height * width * channels) // 8  # Convert bits to bytes
            elif algorithm == "DCT":
                # Approximate capacity for DCT
                return (height * width) // 64  # Conservative estimate
            elif algorithm == "DWT":
                # Approximate capacity for DWT
                return (height * width) // 32  # Conservative estimate
            else:
                return (height * width) // 8  # Default conservative estimate
                
        except Exception as e:
            print(f"Error calculating capacity: {e}")
            return 0
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for steganography"""
        # Ensure image is in correct format
        if len(image.shape) == 2:  # Grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:  # RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        
        return image
    
    def resize_if_needed(self, image: np.ndarray, max_size: Tuple[int, int] = (2048, 2048)) -> np.ndarray:
        """Resize image if it's too large"""
        height, width = image.shape[:2]
        max_height, max_width = max_size
        
        if height > max_height or width > max_width:
            # Calculate scaling factor to maintain aspect ratio
            scale = min(max_height / height, max_width / width)
            new_height = int(height * scale)
            new_width = int(width * scale)
            
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        return image