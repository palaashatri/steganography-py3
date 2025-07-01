import numpy as np
from PIL import Image

class LSBSteganography:
    def __init__(self):
        pass

    def embed(self, image, secret_data):
        """
        Embed secret data into image using LSB steganography
        Args:
            image: numpy array or PIL Image
            secret_data: string or bytes to embed
        Returns:
            Modified image as numpy array
        """
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image.copy()
        
        # Convert secret data to bytes if string
        if isinstance(secret_data, str):
            secret_data = secret_data.encode('utf-8')
        
        # Add delimiter to mark end of data
        secret_data = secret_data + b'\x00\x00\x00\x00'  # 4 null bytes as delimiter
        
        # Convert to binary
        binary_data = ''.join(format(byte, '08b') for byte in secret_data)
        
        # Check if image can hold the data
        total_pixels = image_array.shape[0] * image_array.shape[1]
        if len(image_array.shape) == 3:
            total_capacity = total_pixels * image_array.shape[2]
        else:
            total_capacity = total_pixels
            
        if len(binary_data) > total_capacity:
            raise ValueError(f"Image too small to hold data. Need {len(binary_data)} bits, have {total_capacity}")
        
        # Flatten image for easier processing
        flat_image = image_array.flatten()
        
        # Embed data
        for i, bit in enumerate(binary_data):
            if i < len(flat_image):
                # Clear LSB and set new bit
                flat_image[i] = (flat_image[i] & 0xFE) | int(bit)
        
        # Reshape back to original shape
        return flat_image.reshape(image_array.shape)

    def extract(self, image, max_length=10000):
        """
        Extract secret data from image using LSB steganography
        Args:
            image: numpy array or PIL Image
            max_length: maximum number of bytes to extract
        Returns:
            Extracted string
        """
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image.copy()
        
        # Flatten image
        flat_image = image_array.flatten()
        
        # Extract binary data
        binary_data = ''
        for i in range(min(len(flat_image), max_length * 8)):
            binary_data += str(flat_image[i] & 1)
        
        # Convert binary to bytes
        extracted_bytes = bytearray()
        for i in range(0, len(binary_data), 8):
            if i + 8 <= len(binary_data):
                byte_str = binary_data[i:i+8]
                byte_val = int(byte_str, 2)
                extracted_bytes.append(byte_val)
                
                # Check for delimiter (4 consecutive null bytes)
                if len(extracted_bytes) >= 4:
                    if extracted_bytes[-4:] == bytearray([0, 0, 0, 0]):
                        # Remove delimiter and return
                        extracted_bytes = extracted_bytes[:-4]
                        break
        
        # Convert to string
        try:
            return extracted_bytes.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            return str(extracted_bytes)

    def get_capacity(self, image):
        """
        Calculate the maximum capacity for LSB steganography
        Args:
            image: numpy array or PIL Image
        Returns:
            Maximum bytes that can be embedded
        """
        # Convert PIL Image to numpy array if needed
        if hasattr(image, 'size') and hasattr(image, 'getbands'):  # PIL Image
            width, height = image.size
            channels = len(image.getbands()) if hasattr(image, 'getbands') else 3
        else:  # numpy array
            if len(image.shape) == 3:
                height, width, channels = image.shape
            else:
                height, width = image.shape
                channels = 1
        
        # LSB can embed 1 bit per pixel per channel
        total_bits = height * width * channels
        # Reserve some bits for delimiter (32 bits = 4 bytes)
        usable_bits = total_bits - 32
        
        return max(0, usable_bits // 8)  # Convert to bytes

    # Legacy methods for backward compatibility
    def embed_legacy(self, image_path, secret_data, output_path):
        """Legacy method for backward compatibility"""
        image = Image.open(image_path)
        result_array = self.embed(image, secret_data)
        result_image = Image.fromarray(result_array.astype(np.uint8))
        result_image.save(output_path)

    def extract_legacy(self, image_path):
        """Legacy method for backward compatibility"""
        image = Image.open(image_path)
        return self.extract(image)