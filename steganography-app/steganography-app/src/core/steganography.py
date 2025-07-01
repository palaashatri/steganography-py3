import numpy as np
from PIL import Image
import os
from typing import Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor

from algorithms.lsb import LSBSteganography
from algorithms.dct import DCTSteganography
from algorithms.dwt import DWTSteganography
from algorithms.adaptive import AdaptiveLSB
from core.encryption import EncryptionManager
from utils.image_utils import ImageProcessor
from analysis.quality_metrics import QualityAnalyzer

class SteganographyEngine:
    def __init__(self):
        self.algorithms = {
            'LSB': LSBSteganography(),
            'DCT': DCTSteganography(),
            'DWT': DWTSteganography(),
            'Adaptive LSB': AdaptiveLSB()
        }
        
        self.encryption_manager = EncryptionManager()
        self.image_processor = ImageProcessor()
        self.quality_analyzer = QualityAnalyzer()
        
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def encode_async(self, image_path: str, message: str, password: str = "",
                    algorithm: str = "LSB", encryption_method: str = "AES-256",
                    compression_level: int = 6,
                    progress_callback=None):
        
        def encode_task():
            try:
                image = self.image_processor.load_image(image_path)
                if image is None:
                    raise ValueError("Failed to load image")
                
                if progress_callback:
                    progress_callback(10)
                
                processed_message = self._prepare_message(
                    message, password, encryption_method, compression_level
                )
                
                if progress_callback:
                    progress_callback(30)
                
                # Validate algorithm
                if algorithm not in self.algorithms:
                    raise ValueError(f"Unknown algorithm '{algorithm}'. Available algorithms: {list(self.algorithms.keys())}")
                
                capacity = self.algorithms[algorithm].get_capacity(image)
                if len(processed_message) > capacity:
                    raise ValueError(f"Message too large. Max capacity: {capacity} bytes")
                
                if progress_callback:
                    progress_callback(50)
                
                stego_image = self.algorithms[algorithm].embed(
                    image, processed_message
                )
                
                if progress_callback:
                    progress_callback(80)
                
                analysis = self.quality_analyzer.analyze_quality(image, stego_image)
                
                if progress_callback:
                    progress_callback(100)
                
                return {
                    'success': True,
                    'stego_image': stego_image,
                    'analysis': analysis,
                    'capacity_used': len(processed_message) / capacity * 100
                }
                
            except ValueError as e:
                self.logger.error("Encoding error: %s", str(e))
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return self.executor.submit(encode_task)
    
    def decode_async(self, image_path: str, password: str = "",
                    algorithm: str = "LSB",
                    progress_callback=None):
        
        def decode_task():
            try:
                image = self.image_processor.load_image(image_path)
                if image is None:
                    raise ValueError("Failed to load image")
                
                if progress_callback:
                    progress_callback(20)
                
                # Validate algorithm
                if algorithm not in self.algorithms:
                    raise ValueError(f"Unknown algorithm '{algorithm}'. Available algorithms: {list(self.algorithms.keys())}")
                
                extracted_data = self.algorithms[algorithm].extract(image)
                
                if progress_callback:
                    progress_callback(60)
                
                message = self._process_extracted_data(
                    extracted_data, password
                )
                
                if progress_callback:
                    progress_callback(100)
                
                return {
                    'success': True,
                    'message': message,
                    'data_size': len(extracted_data)
                }
                
            except ValueError as e:
                self.logger.error("Decoding error: %s", str(e))
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return self.executor.submit(decode_task)
    
    def _prepare_message(self, message: str, password: str, 
                        encryption_method: str, compression_level: int) -> bytes:
        message_bytes = message.encode('utf-8')
        
        if compression_level > 0:
            import zlib
            message_bytes = zlib.compress(message_bytes, compression_level)
        
        if password:
            message_bytes = self.encryption_manager.encrypt(
                message_bytes, password, encryption_method
            )
        
        header = self._create_header(password != "", compression_level > 0, encryption_method)
        return header + message_bytes
    
    def _process_extracted_data(self, data: bytes, password: str) -> str:
        header_info = self._parse_header(data)
        message_data = data[header_info['header_size']:]
        
        if header_info['encrypted'] and password:
            message_data = self.encryption_manager.decrypt(
                message_data, password, header_info['encryption_method']
            )
        
        if header_info['compressed']:
            import zlib
            message_data = zlib.decompress(message_data)
        
        return message_data.decode('utf-8')
    
    def _create_header(self, encrypted: bool, compressed: bool, 
                      encryption_method: str) -> bytes:
        flags = 0
        if encrypted:
            flags |= 1
        if compressed:
            flags |= 2
        
        method_map = {'AES-256': 0, 'ChaCha20': 1, 'Fernet': 2}
        method_id = method_map.get(encryption_method, 0)
        
        header = bytes([flags, method_id])
        return header
    
    def _parse_header(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 2:
            raise ValueError("Invalid data format")
        
        flags = data[0]
        method_id = data[1]
        
        method_map = {0: 'AES-256', 1: 'ChaCha20', 2: 'Fernet'}
        
        return {
            'encrypted': bool(flags & 1),
            'compressed': bool(flags & 2),
            'encryption_method': method_map.get(method_id, 'AES-256'),
            'header_size': 2
        }
    
    def get_supported_formats(self) -> list:
        return ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
    
    def validate_image(self, image_path: str) -> bool:
        try:
            image = self.image_processor.load_image(image_path)
            if image is None:
                return False
            
            height, width = image.shape[:2]
            if height < 100 or width < 100:
                return False
            
            return True
        except IOError:
            return False

class Steganography:
    def __init__(self):
        pass

    def embed_data(self, image_path, data, output_path):
        image = Image.open(image_path)
        encoded_image = image.copy()
        data += "EOF"  # End of file marker
        data_bits = ''.join(format(ord(i), '08b') for i in data)
        data_index = 0

        pixels = np.array(encoded_image)
        for i in range(pixels.shape[0]):
            for j in range(pixels.shape[1]):
                pixel = pixels[i][j]
                for k in range(3):  # RGB channels
                    if data_index < len(data_bits):
                        pixel[k] = (pixel[k] & ~1) | int(data_bits[data_index])
                        data_index += 1
                pixels[i][j] = pixel
                if data_index >= len(data_bits):
                    break
            if data_index >= len(data_bits):
                break

        encoded_image = Image.fromarray(pixels)
        encoded_image.save(output_path)

    def extract_data(self, image_path):
        image = Image.open(image_path)
        pixels = np.array(image)
        data_bits = ""

        for i in range(pixels.shape[0]):
            for j in range(pixels.shape[1]):
                pixel = pixels[i][j]
                for k in range(3):  # RGB channels
                    data_bits += str(pixel[k] & 1)

        data = ""
        for i in range(0, len(data_bits), 8):
            byte = data_bits[i:i + 8]
            if byte == "00000000":
                break
            data += chr(int(byte, 2))

        return data.rstrip("EOF")  # Remove the EOF marker

    def validate_image(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError("The specified image file does not exist.")
        if not image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise ValueError("Unsupported image format. Please use PNG or JPG.")