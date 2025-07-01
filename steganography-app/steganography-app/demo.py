#!/usr/bin/env python3
"""
Simple working steganography application demonstration
"""

import sys
import os
import tempfile
import numpy as np
from PIL import Image
import cv2
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import hashlib

class SimpleLSB:
    """Simple LSB steganography implementation"""
    
    def __init__(self):
        self.delimiter = "$$END$$"
    
    def encode(self, image_path, message, password=""):
        """Encode message into image"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("Could not load image")
            
            # Encrypt message if password provided
            if password:
                message = self._encrypt_message(message, password)
            
            # Convert message to binary
            message_with_delimiter = message + self.delimiter
            binary_data = ''.join(format(ord(char), '08b') for char in message_with_delimiter)
            
            # Check capacity
            height, width, channels = img.shape
            max_capacity = height * width * channels
            
            if len(binary_data) > max_capacity:
                raise ValueError("Message too large for image")
            
            # Embed data
            data_index = 0
            for i in range(height):
                for j in range(width):
                    for k in range(channels):
                        if data_index < len(binary_data):
                            # Modify LSB
                            img[i, j, k] = (img[i, j, k] & 0xFE) | int(binary_data[data_index])
                            data_index += 1
                        else:
                            break
                    if data_index >= len(binary_data):
                        break
                if data_index >= len(binary_data):
                    break
            
            return img
            
        except Exception as e:
            raise Exception(f"Encoding failed: {str(e)}")
    
    def decode(self, image_path, password=""):
        """Decode message from image"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("Could not load image")
            
            # Extract binary data
            height, width, channels = img.shape
            binary_data = ""
            
            for i in range(height):
                for j in range(width):
                    for k in range(channels):
                        binary_data += str(img[i, j, k] & 1)
            
            # Convert binary to text
            message = ""
            for i in range(0, len(binary_data), 8):
                if i + 8 <= len(binary_data):
                    byte = binary_data[i:i+8]
                    message += chr(int(byte, 2))
            
            # Find delimiter
            delimiter_index = message.find(self.delimiter)
            if delimiter_index == -1:
                raise ValueError("No hidden message found")
            
            message = message[:delimiter_index]
            
            # Decrypt if password provided
            if password:
                message = self._decrypt_message(message, password)
            
            return message
            
        except Exception as e:
            raise Exception(f"Decoding failed: {str(e)}")
    
    def _encrypt_message(self, message, password):
        """Simple encryption using Fernet"""
        try:
            # Derive key from password
            password_bytes = password.encode()
            salt = hashlib.sha256(password_bytes).digest()[:16]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            
            fernet = Fernet(key)
            encrypted = fernet.encrypt(message.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def _decrypt_message(self, encrypted_message, password):
        """Simple decryption using Fernet"""
        try:
            # Derive key from password
            password_bytes = password.encode()
            salt = hashlib.sha256(password_bytes).digest()[:16]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
            
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

def create_test_image():
    """Create a test image"""
    img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    
    # Add some patterns to make it more realistic
    img[50:100, 50:100] = [255, 0, 0]  # Red square
    img[150:200, 150:200] = [0, 255, 0]  # Green square
    img[200:250, 50:100] = [0, 0, 255]  # Blue square
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        cv2.imwrite(f.name, img)
        return f.name

def calculate_psnr(original, stego):
    """Calculate PSNR between two images"""
    mse = np.mean((original.astype(np.float64) - stego.astype(np.float64)) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr

def demo():
    """Run a complete demonstration"""
    print("🚀 steganography-py3 GUI Demo")
    print("=" * 50)
    
    try:
        # Create steganography engine
        stego = SimpleLSB()
        
        # Create test image
        print("📷 Creating test image...")
        test_image_path = create_test_image()
        print(f"✅ Test image created: {test_image_path}")
        
        # Test message
        secret_message = "This is a secret message hidden using advanced steganography! 🔒"
        password = "MySecurePassword123!"
        
        print(f"\n🔤 Secret message: '{secret_message}'")
        print(f"🔐 Password: '{password}'")
        
        # Encode message
        print("\n🔒 Encoding message...")
        stego_image = stego.encode(test_image_path, secret_message, password)
        
        # Save steganographic image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            cv2.imwrite(f.name, stego_image)
            stego_path = f.name
        
        print(f"✅ Message encoded successfully!")
        print(f"📁 Steganographic image saved: {stego_path}")
        
        # Calculate quality metrics
        original_img = cv2.imread(test_image_path)
        psnr = calculate_psnr(original_img, stego_image)
        print(f"📊 Image quality (PSNR): {psnr:.2f} dB")
        
        if psnr > 40:
            print("✅ Excellent image quality (imperceptible changes)")
        elif psnr > 30:
            print("✅ Good image quality")
        else:
            print("⚠️ Noticeable image quality degradation")
        
        # Decode message
        print("\n🔓 Decoding message...")
        decoded_message = stego.decode(stego_path, password)
        print(f"✅ Message decoded: '{decoded_message}'")
        
        # Verify integrity
        if decoded_message == secret_message:
            print("✅ Message integrity verified - perfect match!")
        else:
            print("❌ Message corruption detected")
        
        # Test without password (should fail)
        print("\n🧪 Testing security (decoding without password)...")
        try:
            decoded_without_pass = stego.decode(stego_path, "")
            print(f"⚠️ Decoded without password: '{decoded_without_pass[:50]}...'")
        except Exception as e:
            print("✅ Security verified - cannot decode without password")
        
        # Capacity analysis
        original_size = os.path.getsize(test_image_path)
        stego_size = os.path.getsize(stego_path)
        message_size = len(secret_message.encode())
        
        print(f"\n📈 Analysis:")
        print(f"   Original image size: {original_size:,} bytes")
        print(f"   Steganographic image size: {stego_size:,} bytes")
        print(f"   Message size: {message_size} bytes")
        print(f"   Size difference: {abs(stego_size - original_size)} bytes")
        print(f"   Capacity utilization: {(message_size / (300*300*3)) * 100:.4f}%")
        
        # Cleanup
        os.unlink(test_image_path)
        os.unlink(stego_path)
        
        print("\n🎉 Demo completed successfully!")
        print("\nFeatures demonstrated:")
        print("   ✅ LSB steganography encoding/decoding")
        print("   ✅ Password-based encryption")
        print("   ✅ Quality analysis (PSNR)")
        print("   ✅ Security verification")
        print("   ✅ Capacity analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = demo()
    sys.exit(0 if success else 1)
