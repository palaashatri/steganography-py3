from scipy.fftpack import dct, idct
import numpy as np

class DCTSteganography:
    def __init__(self, image=None):
        self.image = image
        self.coefficients = None

    def embed(self, image, secret_data):
        """Standard embed method compatible with SteganographyEngine"""
        self.image = image
        if isinstance(secret_data, str):
            secret_data = secret_data.encode('utf-8')
        return self.embed_data(secret_data)

    def embed_data(self, data):
        data_bits = self._string_to_bits(data)
        self.coefficients = dct(dct(self.image, axis=0), axis=1)
        
        # Embed data into the DCT coefficients
        for i in range(len(data_bits)):
            self.coefficients[i // self.image.shape[1], i % self.image.shape[1]] = (
                self.coefficients[i // self.image.shape[1], i % self.image.shape[1]] & ~1 | data_bits[i]
            )
        
        return idct(idct(self.coefficients, axis=0), axis=1)

    def extract(self, image, expected_length=None):
        """Standard extract method compatible with SteganographyEngine"""
        self.image = image
        if expected_length is None:
            expected_length = 1000  # Default length
        extracted_data = self.extract_data(expected_length)
        try:
            return extracted_data.decode('utf-8').rstrip('\x00')
        except UnicodeDecodeError:
            return str(extracted_data)

    def extract_data(self, length):
        if self.coefficients is None:
            raise ValueError("No data has been embedded.")
        
        extracted_bits = []
        for i in range(length):
            extracted_bits.append(int(self.coefficients[i // self.image.shape[1], i % self.image.shape[1]] % 2))
        
        return self._bits_to_string(extracted_bits)

    def _string_to_bits(self, data):
        return [int(bit) for char in data for bit in format(ord(char), '08b')]

    def _bits_to_string(self, bits):
        chars = [chr(int(''.join(map(str, bits[i:i + 8])), 2)) for i in range(0, len(bits), 8)]
        return ''.join(chars)

    def get_capacity(self, image):
        """
        Calculate the maximum capacity for DCT steganography
        Args:
            image: numpy array
        Returns:
            Maximum bytes that can be embedded
        """
        if len(image.shape) == 3:
            height, width, channels = image.shape
        else:
            height, width = image.shape
            channels = 1
        
        # DCT works on 8x8 blocks, so capacity is limited
        blocks_h = height // 8
        blocks_w = width // 8
        total_blocks = blocks_h * blocks_w * channels
        
        # Conservative estimate - we can embed in mid-frequency coefficients
        # Typically we can embed 1-2 bits per block safely
        usable_bits = total_blocks * 1  # 1 bit per block
        
        return max(0, usable_bits // 8)  # Convert to bytes