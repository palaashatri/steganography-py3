import numpy as np
from scipy.fftpack import dct, idct

class AdaptiveLSB:
    def __init__(self, image=None):
        self.image = image

    def embed_data(self, data):
        # Convert data to binary
        binary_data = ''.join(format(byte, '08b') for byte in data)
        data_length = len(binary_data)
        data_index = 0

        # Perform DCT on the image
        dct_image = dct(dct(self.image, axis=0), axis=1)

        # Embed data into the DCT coefficients
        for i in range(dct_image.shape[0]):
            for j in range(dct_image.shape[1]):
                if data_index < data_length:
                    # Modify the DCT coefficient based on the binary data
                    if binary_data[data_index] == '1':
                        dct_image[i][j] += 1  # Example modification
                    else:
                        dct_image[i][j] -= 1  # Example modification
                    data_index += 1

        # Perform inverse DCT to get the stego image
        stego_image = idct(idct(dct_image, axis=0), axis=1)
        return stego_image

    def extract_data(self, length):
        binary_data = ''
        
        # Perform DCT on the image
        dct_image = dct(dct(self.image, axis=0), axis=1)

        # Extract data from the DCT coefficients
        for i in range(dct_image.shape[0]):
            for j in range(dct_image.shape[1]):
                if len(binary_data) < length:
                    # Check the least significant bit of the DCT coefficient
                    if dct_image[i][j] % 2 == 1:
                        binary_data += '1'
                    else:
                        binary_data += '0'

        # Convert binary data to bytes
        data = bytearray()
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            data.append(int(byte, 2))
        
        return data

    def embed(self, image, secret_data):
        """Standard embed method compatible with SteganographyEngine"""
        self.image = image
        if isinstance(secret_data, str):
            secret_data = secret_data.encode('utf-8')
        return self.embed_data(secret_data)
    
    def extract(self, image, expected_length=None):
        """Standard extract method compatible with SteganographyEngine"""
        self.image = image
        if expected_length is None:
            expected_length = 1000  # Default length
        extracted_bytes = self.extract_data(expected_length * 8)  # Convert to bits
        try:
            return extracted_bytes.decode('utf-8').rstrip('\x00')
        except UnicodeDecodeError:
            return str(extracted_bytes)

    def get_capacity(self, image):
        """
        Calculate the maximum capacity for Adaptive LSB steganography
        Args:
            image: numpy array
        Returns:
            Maximum bytes that can be embedded
        """
        if image is None:
            # Use provided image if available
            image = self.image
            
        if image is None:
            return 0
            
        if len(image.shape) == 3:
            height, width, channels = image.shape
        else:
            height, width = image.shape
            channels = 1
        
        # Adaptive LSB has variable capacity based on image complexity
        # For simplicity, estimate 70% of LSB capacity (adaptive selection)
        total_bits = height * width * channels
        adaptive_ratio = 0.7  # Only use smooth regions
        usable_bits = int(total_bits * adaptive_ratio) - 32  # Reserve for delimiter
        
        return max(0, usable_bits // 8)  # Convert to bytes