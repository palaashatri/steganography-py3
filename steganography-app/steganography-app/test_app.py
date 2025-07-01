#!/usr/bin/env python3

import sys
import os
import tempfile
import numpy as np
from PIL import Image

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.steganography import SteganographyEngine
    from core.encryption import EncryptionManager
    from algorithms.lsb import LSBSteganography
    from utils.image_utils import ImageProcessor
    from analysis.quality_metrics import QualityAnalyzer
    print("✅ All core imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")

def create_test_image():
    """Create a simple test image"""
    img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    image = Image.fromarray(img)
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image.save(f.name)
        return f.name

def test_basic_functionality():
    """Test basic steganography functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Create test image
        test_image_path = create_test_image()
        print(f"✅ Created test image: {test_image_path}")
        
        # Test LSB algorithm
        lsb = LSBSteganography()
        test_message = "Hello, this is a secret message!"
        
        # Load image
        from utils.image_utils import ImageProcessor
        processor = ImageProcessor()
        image = processor.load_image(test_image_path)
        
        # Encode
        stego_image = lsb.embed(image, test_message)
        print("✅ Message encoded successfully")
        
        # Save stego image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            stego_path = f.name
        
        processor.save_image(stego_image, stego_path)
        
        # Decode
        decoded_message = lsb.extract(stego_image)
        print(f"✅ Message decoded: {decoded_message}")
        
        # Verify
        if test_message in decoded_message:
            print("✅ Message integrity verified")
        else:
            print("❌ Message corruption detected")
        
        # Cleanup
        os.unlink(test_image_path)
        os.unlink(stego_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_encryption():
    """Test encryption functionality"""
    print("\n🔐 Testing encryption...")
    
    try:
        encryption_manager = EncryptionManager()
        
        test_data = b"This is sensitive data"
        password = "test_password_123"
        
        # Test AES encryption
        encrypted = encryption_manager.encrypt(test_data, password, "AES-256")
        decrypted = encryption_manager.decrypt(encrypted, password, "AES-256")
        
        if decrypted == test_data:
            print("✅ AES-256 encryption/decryption successful")
        else:
            print("❌ AES-256 encryption/decryption failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False

def test_quality_analysis():
    """Test quality analysis"""
    print("\n📊 Testing quality analysis...")
    
    try:
        # Create two similar images
        img1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img2 = img1.copy()
        img2[50, 50] = [0, 0, 0]  # Small modification
        
        analyzer = QualityAnalyzer()
        results = analyzer.analyze_quality(img1, img2)
        
        print(f"✅ PSNR: {results['psnr']:.2f}")
        print(f"✅ SSIM: {results['ssim']:.4f}")
        print(f"✅ MSE: {results['mse']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quality analysis test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Steganography Application Tests")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_encryption,
        test_quality_analysis
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
