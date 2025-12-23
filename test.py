#!/usr/bin/env python3
"""
Test suite for steganography application.
Demonstrates all functionality: LSB image steganography and MP3 embedding.
"""

import subprocess
import tempfile
import os
from pathlib import Path
from PIL import Image


def run_cmd(args):
    """Run a command and return success status."""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {' '.join(args)}")
        print(f"Error: {result.stderr}")
        return False
    return True


def create_test_image(path, width=100, height=100, color='red'):
    """Create a simple test image."""
    img = Image.new('RGB', (width, height), color=color)
    img.save(path)
    return path


def create_test_mp3(path):
    """Create a dummy MP3 file (just for ID3 testing)."""
    # Write minimal MP3-like binary to satisfy mutagen
    with open(path, 'wb') as f:
        # ID3v2 header
        f.write(b'ID3')
        f.write(b'\x03\x00')  # version
        f.write(b'\x00')       # flags
        f.write(b'\x00\x00\x00\x00')  # size
        # Some dummy MP3 frames
        f.write(b'\xff\xfb\x10\x00' * 100)  # Fake MP3 frames


def create_test_mp4(path):
    """Create a dummy MP4 file with minimal moov atom for testing."""
    with open(path, 'wb') as f:
        # ftyp box (32 bytes)
        f.write(b'\x00\x00\x00\x20')  # size = 32
        f.write(b'ftyp')               # type
        f.write(b'isom')               # brand
        f.write(b'\x00\x00\x02\x00')  # minor version
        f.write(b'isomiso2mp41iso6')   # compatible brands (12 bytes)
        
        # Minimal moov box with mvhd (movie header)
        # moov size will be calculated
        moov_content = b''
        
        # mvhd box (100 bytes for version 0)
        mvhd = b'\x00\x00\x00\x6c'     # size = 108
        mvhd += b'mvhd'                # type
        mvhd += b'\x00'                # version = 0
        mvhd += b'\x00\x00\x00'        # flags = 0
        mvhd += b'\x00\x00\x00\x00'    # creation time
        mvhd += b'\x00\x00\x00\x00'    # modification time
        mvhd += b'\x00\x00\x03\xe8'    # timescale = 1000
        mvhd += b'\x00\x00\x00\x00'    # duration = 0
        mvhd += b'\x00\x01\x00\x00'    # playback speed = 1.0
        mvhd += b'\x01\x00'            # volume = 1.0
        mvhd += b'\x00' * 10           # reserved
        mvhd += b'\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00'  # matrix
        mvhd += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # matrix
        mvhd += b'\x00\x00\x00\x02'    # next track ID = 2
        
        moov_content = mvhd
        
        # moov box header + content
        moov_size = 8 + len(moov_content)
        moov = moov_size.to_bytes(4, 'big') + b'moov' + moov_content
        f.write(moov)


def test_image_lsb_steganography(tmpdir):
    """Test basic LSB image steganography."""
    print("\n" + "="*60)
    print("TEST 1: LSB Image Steganography")
    print("="*60)
    
    # Create test image
    cover_img = create_test_image(os.path.join(tmpdir, 'cover.png'), 500, 500)
    stego_img = os.path.join(tmpdir, 'stego.png')
    extracted_text = os.path.join(tmpdir, 'extracted.txt')
    
    # Embed text
    print("\n1. Embedding text into image...")
    secret_msg = "This is a secret message hidden in an image!"
    if not run_cmd(['python3', '1_Implementation/app.py', 'encode',
                    '--image', cover_img,
                    '--out', stego_img,
                    '--message', secret_msg]):
        return False
    print("✓ Text embedded successfully")
    
    # Extract text
    print("2. Extracting text from image...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'decode',
                    '--image', stego_img,
                    '--out', extracted_text]):
        return False
    
    # Verify
    with open(extracted_text, 'r') as f:
        extracted = f.read()
    if extracted == secret_msg:
        print("✓ Text extracted and verified correctly!")
        return True
    else:
        print(f"❌ Extracted text doesn't match!\nExpected: {secret_msg}\nGot: {extracted}")
        return False


def test_image_lsb_with_encryption(tmpdir):
    """Test LSB steganography with encryption."""
    print("\n" + "="*60)
    print("TEST 2: LSB with Encryption")
    print("="*60)
    
    cover_img = create_test_image(os.path.join(tmpdir, 'cover2.png'), 500, 500)
    stego_img = os.path.join(tmpdir, 'stego_encrypted.png')
    extracted_text = os.path.join(tmpdir, 'extracted_encrypted.txt')
    
    # Embed with encryption
    print("\n1. Embedding encrypted text into image...")
    secret_msg = "Super secret encrypted message!"
    password = "mypassword123"
    if not run_cmd(['python3', '1_Implementation/app.py', 'encode',
                    '--image', cover_img,
                    '--out', stego_img,
                    '--message', secret_msg,
                    '--password', password]):
        return False
    print("✓ Encrypted text embedded")
    
    # Extract with correct password
    print("2. Extracting with correct password...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'decode',
                    '--image', stego_img,
                    '--out', extracted_text,
                    '--password', password]):
        return False
    
    with open(extracted_text, 'r') as f:
        extracted = f.read()
    if extracted == secret_msg:
        print("✓ Encrypted text verified!")
        return True
    else:
        print(f"❌ Decrypted text doesn't match!")
        return False


def test_mp3_text_embedding(tmpdir):
    """Test embedding text in MP3 files."""
    print("\n" + "="*60)
    print("TEST 3: MP3 Text Embedding")
    print("="*60)
    
    mp3_file = os.path.join(tmpdir, 'test.mp3')
    create_test_mp3(mp3_file)
    output_mp3 = os.path.join(tmpdir, 'test_with_text.mp3')
    extracted_text = os.path.join(tmpdir, 'mp3_extracted.txt')
    
    # Embed text in MP3
    print("\n1. Embedding text into MP3...")
    secret_text = "Hidden in MP3 metadata!"
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-encode',
                    '--mp3', mp3_file,
                    '--out', output_mp3,
                    '--message', secret_text]):
        return False
    print("✓ Text embedded in MP3")
    
    # Extract text from MP3
    print("2. Extracting text from MP3...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-decode',
                    '--mp3', output_mp3,
                    '--out', extracted_text]):
        return False
    
    with open(extracted_text, 'rb') as f:
        extracted = f.read().decode('utf-8')
    if extracted == secret_text:
        print("✓ MP3 text verified!")
        return True
    else:
        print(f"❌ MP3 extracted text doesn't match!")
        return False


def test_mp3_image_embedding(tmpdir):
    """Test embedding images in MP3 files."""
    print("\n" + "="*60)
    print("TEST 4: MP3 Image Embedding")
    print("="*60)
    
    # Create test image
    secret_img = create_test_image(os.path.join(tmpdir, 'secret.png'), 50, 50, 'blue')
    mp3_file = os.path.join(tmpdir, 'test2.mp3')
    create_test_mp3(mp3_file)
    output_mp3 = os.path.join(tmpdir, 'test_with_image.mp3')
    extracted_img = os.path.join(tmpdir, 'mp3_extracted.png')
    
    # Embed image in MP3
    print("\n1. Embedding image into MP3...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-encode',
                    '--mp3', mp3_file,
                    '--out', output_mp3,
                    '--image', secret_img]):
        return False
    print("✓ Image embedded in MP3")
    
    # Extract image from MP3
    print("2. Extracting image from MP3...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-decode',
                    '--mp3', output_mp3,
                    '--out', extracted_img]):
        return False
    
    # Verify image exists and is valid
    if os.path.exists(extracted_img):
        extracted_image = Image.open(extracted_img)
        orig_image = Image.open(secret_img)
        if extracted_image.size == orig_image.size:
            print("✓ MP3 image verified!")
            return True
    print("❌ MP3 image extraction failed!")
    return False


def test_mp3_file_embedding(tmpdir):
    """Test embedding arbitrary files in MP3."""
    print("\n" + "="*60)
    print("TEST 5: MP3 File Embedding")
    print("="*60)
    
    # Create test file
    test_file = os.path.join(tmpdir, 'secret.bin')
    test_data = b"Binary file content \x00\x01\x02\xff\xfe"
    with open(test_file, 'wb') as f:
        f.write(test_data)
    
    mp3_file = os.path.join(tmpdir, 'test3.mp3')
    create_test_mp3(mp3_file)
    output_mp3 = os.path.join(tmpdir, 'test_with_file.mp3')
    extracted_file = os.path.join(tmpdir, 'mp3_extracted.bin')
    
    # Embed file in MP3
    print("\n1. Embedding file into MP3...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-encode',
                    '--mp3', mp3_file,
                    '--out', output_mp3,
                    '--in-file', test_file]):
        return False
    print("✓ File embedded in MP3")
    
    # Extract file from MP3
    print("2. Extracting file from MP3...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-decode',
                    '--mp3', output_mp3,
                    '--out', extracted_file]):
        return False
    
    # Verify
    with open(extracted_file, 'rb') as f:
        extracted = f.read()
    if extracted == test_data:
        print("✓ MP3 file verified!")
        return True
    else:
        print("❌ MP3 file extraction failed!")
        return False


def test_mp3_encrypted_embedding(tmpdir):
    """Test encrypted MP3 embedding."""
    print("\n" + "="*60)
    print("TEST 6: MP3 Encrypted Embedding")
    print("="*60)
    
    mp3_file = os.path.join(tmpdir, 'test4.mp3')
    create_test_mp3(mp3_file)
    output_mp3 = os.path.join(tmpdir, 'test_encrypted.mp3')
    extracted_text = os.path.join(tmpdir, 'mp3_encrypted_extracted.txt')
    
    secret_text = "Encrypted MP3 content"
    password = "secretpass456"
    
    # Embed encrypted text
    print("\n1. Embedding encrypted text into MP3...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-encode',
                    '--mp3', mp3_file,
                    '--out', output_mp3,
                    '--message', secret_text,
                    '--password', password]):
        return False
    print("✓ Encrypted text embedded in MP3")
    
    # Extract with password
    print("2. Extracting encrypted text from MP3...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp3-decode',
                    '--mp3', output_mp3,
                    '--out', extracted_text,
                    '--password', password]):
        return False
    
    with open(extracted_text, 'rb') as f:
        extracted = f.read().decode('utf-8')
    if extracted == secret_text:
        print("✓ Encrypted MP3 verified!")
        return True
    else:
        print("❌ Encrypted MP3 extraction failed!")
        return False


def test_mp4_text_embedding(tmpdir):
    """Test embedding text in MP4 files."""
    print("\n" + "="*60)
    print("TEST 7: MP4 Text Embedding")
    print("="*60)
    
    mp4_file = os.path.join(tmpdir, 'test.mp4')
    create_test_mp4(mp4_file)
    output_mp4 = os.path.join(tmpdir, 'test_with_text.mp4')
    extracted_text = os.path.join(tmpdir, 'mp4_extracted.txt')
    
    # Embed text in MP4
    print("\n1. Embedding text into MP4...")
    secret_text = "Hidden in MP4 metadata!"
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-encode',
                    '--mp4', mp4_file,
                    '--out', output_mp4,
                    '--message', secret_text]):
        return False
    print("✓ Text embedded in MP4")
    
    # Extract text from MP4
    print("2. Extracting text from MP4...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-decode',
                    '--mp4', output_mp4,
                    '--out', extracted_text]):
        return False
    
    with open(extracted_text, 'rb') as f:
        extracted = f.read().decode('utf-8')
    if extracted == secret_text:
        print("✓ MP4 text verified!")
        return True
    else:
        print(f"❌ MP4 extracted text doesn't match!")
        return False


def test_mp4_image_embedding(tmpdir):
    """Test embedding images in MP4 files."""
    print("\n" + "="*60)
    print("TEST 8: MP4 Image Embedding")
    print("="*60)
    
    # Create test image
    secret_img = create_test_image(os.path.join(tmpdir, 'secret.png'), 50, 50, 'green')
    mp4_file = os.path.join(tmpdir, 'test2.mp4')
    create_test_mp4(mp4_file)
    output_mp4 = os.path.join(tmpdir, 'test_with_image.mp4')
    extracted_img = os.path.join(tmpdir, 'mp4_extracted.png')
    
    # Embed image in MP4
    print("\n1. Embedding image into MP4...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-encode',
                    '--mp4', mp4_file,
                    '--out', output_mp4,
                    '--image', secret_img]):
        return False
    print("✓ Image embedded in MP4")
    
    # Extract image from MP4
    print("2. Extracting image from MP4...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-decode',
                    '--mp4', output_mp4,
                    '--out', extracted_img]):
        return False
    
    # Verify image exists and is valid
    if os.path.exists(extracted_img):
        extracted_image = Image.open(extracted_img)
        orig_image = Image.open(secret_img)
        if extracted_image.size == orig_image.size:
            print("✓ MP4 image verified!")
            return True
    print("❌ MP4 image extraction failed!")
    return False


def test_mp4_mp3_embedding(tmpdir):
    """Test embedding MP3 files in MP4."""
    print("\n" + "="*60)
    print("TEST 9: MP4 MP3 Embedding")
    print("="*60)
    
    # Create test MP3
    test_mp3 = os.path.join(tmpdir, 'secret.mp3')
    create_test_mp3(test_mp3)
    
    mp4_file = os.path.join(tmpdir, 'test3.mp4')
    create_test_mp4(mp4_file)
    output_mp4 = os.path.join(tmpdir, 'test_with_mp3.mp4')
    extracted_mp3 = os.path.join(tmpdir, 'mp4_extracted.mp3')
    
    # Embed MP3 in MP4
    print("\n1. Embedding MP3 into MP4...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-encode',
                    '--mp4', mp4_file,
                    '--out', output_mp4,
                    '--mp3', test_mp3]):
        return False
    print("✓ MP3 embedded in MP4")
    
    # Extract MP3 from MP4
    print("2. Extracting MP3 from MP4...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-decode',
                    '--mp4', output_mp4,
                    '--out', extracted_mp3]):
        return False
    
    # Verify
    if os.path.exists(extracted_mp3) and os.path.getsize(extracted_mp3) > 0:
        print("✓ MP4 MP3 verified!")
        return True
    else:
        print("❌ MP4 MP3 extraction failed!")
        return False


def test_mp4_encrypted_embedding(tmpdir):
    """Test encrypted MP4 embedding."""
    print("\n" + "="*60)
    print("TEST 10: MP4 Encrypted Embedding")
    print("="*60)
    
    mp4_file = os.path.join(tmpdir, 'test4.mp4')
    create_test_mp4(mp4_file)
    output_mp4 = os.path.join(tmpdir, 'test_encrypted.mp4')
    extracted_text = os.path.join(tmpdir, 'mp4_encrypted_extracted.txt')
    
    secret_text = "Encrypted MP4 content"
    password = "secretpass789"
    
    # Embed encrypted text
    print("\n1. Embedding encrypted text into MP4...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-encode',
                    '--mp4', mp4_file,
                    '--out', output_mp4,
                    '--message', secret_text,
                    '--password', password]):
        return False
    print("✓ Encrypted text embedded in MP4")
    
    # Extract with password
    print("2. Extracting encrypted text from MP4...")
    if not run_cmd(['python3', '1_Implementation/app.py', 'mp4-decode',
                    '--mp4', output_mp4,
                    '--out', extracted_text,
                    '--password', password]):
        return False
    
    with open(extracted_text, 'rb') as f:
        extracted = f.read().decode('utf-8')
    if extracted == secret_text:
        print("✓ Encrypted MP4 verified!")
        return True
    else:
        print("❌ Encrypted MP4 extraction failed!")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("STEGANOGRAPHY TEST SUITE")
    print("="*60)
    print("\nTesting all features of the steganography suite:")
    print("- LSB image steganography")
    print("- MP3 text/file/image embedding")
    print("- MP4 text/file/image/MP3 embedding")
    print("- Encryption support")
    
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tests = [
            ("LSB Steganography", test_image_lsb_steganography),
            ("LSB with Encryption", test_image_lsb_with_encryption),
            ("MP3 Text Embedding", test_mp3_text_embedding),
            ("MP3 Image Embedding", test_mp3_image_embedding),
            ("MP3 File Embedding", test_mp3_file_embedding),
            ("MP3 Encrypted Embedding", test_mp3_encrypted_embedding),
            ("MP4 Text Embedding", test_mp4_text_embedding),
            ("MP4 Image Embedding", test_mp4_image_embedding),
            ("MP4 MP3 Embedding", test_mp4_mp3_embedding),
            ("MP4 Encrypted Embedding", test_mp4_encrypted_embedding),
        ]
        
        for name, test_func in tests:
            try:
                result = test_func(tmpdir)
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ {name} failed with exception: {e}")
                results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == '__main__':
    exit(main())
