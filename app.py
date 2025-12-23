"""Command-line LSB steganography with optional AES-GCM protection.

Features:
- Fixed header with magic bytes and payload length (no LSB end-flag).
- Optional AES-256-GCM encryption with password-based key derivation.
- Capacity checks before embedding to prevent partial writes.
- Binary payload support (text or file input).
- Argparse CLI for scripting; logging for diagnostics.
"""

from __future__ import annotations

import argparse
import base64
import logging
import os
import random
import hashlib
from dataclasses import dataclass
from typing import List, Sequence

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PIL import Image
from mutagen.id3 import ID3, APIC, TIT2, TPE1
from mutagen.mp4 import MP4


MAGIC = b"STG1"
VERSION = 1
FLAG_ENCRYPTED = 0b0000_0001
FLAG_PRNG = 0b0000_0010
FLAG_LSB_MATCH = 0b0000_0100
FLAG_PAYLOAD_IMAGE = 0b0000_1000  # Payload is image data (MP3/MP4 only)
FLAG_PAYLOAD_TEXT = 0b0001_0000   # Payload is text/file data (MP3/MP4 only)
FLAG_PAYLOAD_MP3 = 0b0010_0000    # Payload is MP3 file (MP4 only)

DEFAULT_SALT_LEN = 16
DEFAULT_NONCE_LEN = 12
PBKDF2_ITERATIONS = 200_000
KEY_LEN = 32  # AES-256


@dataclass
class StegoHeader:
    flags: int
    salt: bytes
    nonce: bytes
    payload_len: int

    def to_bytes(self) -> bytes:
        salt_len = len(self.salt)
        nonce_len = len(self.nonce)
        header = bytearray()
        header += MAGIC
        header.append(VERSION)
        header.append(self.flags)
        header.append(salt_len)
        header.append(nonce_len)
        header += self.payload_len.to_bytes(4, byteorder="big", signed=False)
        header += self.salt
        header += self.nonce
        return bytes(header)


def parse_header(raw: bytes) -> StegoHeader:
    if len(raw) < 12:
        raise ValueError("Header too short; not a valid stego payload")

    magic = raw[0:4]
    if magic != MAGIC:
        raise ValueError("Magic bytes mismatch; not a supported stego image")

    version = raw[4]
    if version != VERSION:
        raise ValueError(f"Unsupported version {version}; expected {VERSION}")

    flags = raw[5]
    salt_len = raw[6]
    nonce_len = raw[7]
    payload_len = int.from_bytes(raw[8:12], byteorder="big", signed=False)

    expected_len = 12 + salt_len + nonce_len
    if len(raw) < expected_len:
        raise ValueError("Header incomplete; missing salt or nonce bytes")

    salt = raw[12 : 12 + salt_len]
    nonce = raw[12 + salt_len : 12 + salt_len + nonce_len]
    return StegoHeader(flags=flags, salt=salt, nonce=nonce, payload_len=payload_len)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def bytes_to_bits(data: bytes) -> List[int]:
    return [(byte >> shift) & 1 for byte in data for shift in range(7, -1, -1)]


def bits_to_bytes(bits: Sequence[int]) -> bytes:
    if len(bits) % 8 != 0:
        raise ValueError("Bit length must be a multiple of 8")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for shift, bit in enumerate(bits[i : i + 8]):
            byte |= (bit & 1) << (7 - shift)
        out.append(byte)
    return bytes(out)


def flatten_channels(image: Image.Image) -> List[int]:
    channels: List[int] = []
    for r, g, b in image.getdata():
        channels.extend((r, g, b))
    return channels


def rebuild_image(channels: Sequence[int], size: tuple[int, int]) -> Image.Image:
    pixels = [tuple(channels[i : i + 3]) for i in range(0, len(channels), 3)]
    new_img = Image.new("RGB", size)
    new_img.putdata(pixels)
    return new_img


def embed_bits(base_image: Image.Image, bits: Sequence[int]) -> Image.Image:
    channels = flatten_channels(base_image)
    if len(bits) > len(channels):
        raise ValueError(
            f"Payload too large: need {len(bits)} bits but image only has {len(channels)} LSBs"
        )

    updated = channels.copy()
    for idx, bit in enumerate(bits):
        value = updated[idx]
        if (value & 1) != bit:
            updated[idx] = value ^ 1 if value != 0 else 1
    return rebuild_image(updated, base_image.size)


def _permute_indices(length: int, rng: random.Random) -> List[int]:
    idxs = list(range(length))
    rng.shuffle(idxs)
    return idxs


def make_rng(key: str) -> random.Random:
    # Deterministic seed from key using SHA-256
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def embed_bits_prng(base_image: Image.Image, bits: Sequence[int], rng: random.Random, lsb_match: bool = False) -> Image.Image:
    channels = flatten_channels(base_image)
    if len(bits) > len(channels):
        raise ValueError(
            f"Payload too large: need {len(bits)} bits but image only has {len(channels)} LSBs"
        )

    updated = channels.copy()
    indices = _permute_indices(len(channels), rng)
    for i, bit in enumerate(bits):
        idx = indices[i]
        value = updated[idx]
        if (value & 1) != bit:
            if lsb_match:
                if value == 0:
                    updated[idx] = 1
                elif value == 255:
                    updated[idx] = 254
                else:
                    updated[idx] = value + (1 if rng.random() < 0.5 else -1)
            else:
                updated[idx] = value ^ 1 if value != 0 else 1
    return rebuild_image(updated, base_image.size)


def extract_bits(image: Image.Image, count: int) -> List[int]:
    channels = flatten_channels(image)
    if count > len(channels):
        raise ValueError(
            f"Requested {count} bits but image only has {len(channels)} LSBs"
        )
    return [(value & 1) for value in channels[:count]]


def extract_bits_prng(image: Image.Image, count: int, rng: random.Random) -> List[int]:
    channels = flatten_channels(image)
    if count > len(channels):
        raise ValueError(
            f"Requested {count} bits but image only has {len(channels)} LSBs"
        )
    indices = _permute_indices(len(channels), rng)
    return [(channels[idx] & 1) for idx in indices[:count]]


def max_payload_bytes(image: Image.Image) -> int:
    total_bits = image.size[0] * image.size[1] * 3
    return total_bits // 8


def build_aad(flags: int, salt: bytes, nonce: bytes) -> bytes:
    return MAGIC + bytes([VERSION, flags]) + salt + nonce


def load_image(path: str) -> Image.Image:
    try:
        img = Image.open(path).convert("RGB")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Image not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Could not open image '{path}': {exc}") from exc
    return img


def load_mp3(path: str) -> None:
    """Load and validate MP3 file exists."""
    try:
        with open(path, "rb") as f:
            pass
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"MP3 file not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Could not open MP3 file '{path}': {exc}") from exc


def embed_data_in_mp3(mp3_path: str, output_path: str, password: str | None = None, 
                      message: str | None = None, in_file: str | None = None, 
                      image_path: str | None = None) -> None:
    """Embed text/file data or image into an MP3 file using ID3 tags with optional encryption."""
    import shutil
    
    load_mp3(mp3_path)
    
    # Determine payload type
    payload_count = sum([message is not None, in_file is not None, image_path is not None])
    if payload_count == 0:
        raise ValueError("Provide --message, --in-file, or --image")
    if payload_count > 1:
        raise ValueError("Provide only one of: --message, --in-file, or --image")
    
    flags = 0
    salt = b""
    nonce = b""
    plaintext = b""
    metadata = b""  # Additional metadata after payload
    
    if image_path:
        # Handle image embedding
        flags |= FLAG_PAYLOAD_IMAGE
        image = load_image(image_path)
        
        # Convert image to bytes
        image_bytes = bytearray()
        for pixel in image.getdata():
            image_bytes.extend(pixel)
        plaintext = bytes(image_bytes)
        
        # Store image dimensions in metadata
        metadata = image.size[0].to_bytes(4, byteorder="big") + image.size[1].to_bytes(4, byteorder="big")
    else:
        # Handle text/file embedding
        flags |= FLAG_PAYLOAD_TEXT
        if message:
            plaintext = message.encode("utf-8")
        else:
            assert in_file is not None
            with open(in_file, "rb") as f:
                plaintext = f.read()
    
    # Encrypt (optional)
    payload_bytes = plaintext
    if password:
        flags |= FLAG_ENCRYPTED
        salt = os.urandom(DEFAULT_SALT_LEN)
        nonce = os.urandom(DEFAULT_NONCE_LEN)
        key = derive_key(password, salt)
        aad = build_aad(flags, salt, nonce)
        payload_bytes = AESGCM(key).encrypt(nonce, plaintext, aad)
    
    # Create header
    header = StegoHeader(flags=flags, salt=salt, nonce=nonce, payload_len=len(payload_bytes)).to_bytes()
    stego_data = header + payload_bytes + metadata
    
    # Load or create ID3 tag
    try:
        tags = ID3(mp3_path)
    except:
        tags = ID3()
    
    # Store embedded data in APIC (Attached Picture) frame as binary data
    tags["APIC"] = APIC(
        encoding=3,
        mime="application/octet-stream",
        type=0,
        desc="STEG_DATA",
        data=stego_data
    )
    
    # Save to output file
    shutil.copy(mp3_path, output_path)
    tags.save(output_path, v2_version=3)
    
    payload_type = "image" if (flags & FLAG_PAYLOAD_IMAGE) else "text/file"
    logging.info("Embedded %s in MP3: %s", payload_type, output_path)


def extract_data_from_mp3(mp3_path: str, output_path: str, password: str | None = None) -> None:
    """Extract text/file data or image from an MP3 file's ID3 tags with optional decryption."""
    load_mp3(mp3_path)
    
    try:
        tags = ID3(mp3_path)
    except:
        raise ValueError("No ID3 tags found in MP3 file")
    
    # Extract stego data from APIC frame
    # The frame key includes the description: "APIC:STEG_DATA"
    apic_frame = None
    for key in tags.keys():
        if key.startswith("APIC"):
            apic_frame = tags[key]
            break
    
    if apic_frame is None:
        raise ValueError("No embedded data found in MP3 file")
    
    stego_data = apic_frame.data
    
    # Parse header
    cursor = 0
    
    def read_bytes(num_bytes: int) -> bytes:
        nonlocal cursor
        data = stego_data[cursor:cursor + num_bytes]
        cursor += num_bytes
        return data
    
    header_prefix = read_bytes(12)
    salt_len = header_prefix[6]
    nonce_len = header_prefix[7]
    
    extra_header = b""
    if salt_len + nonce_len > 0:
        extra_header = read_bytes(salt_len + nonce_len)
    
    header = parse_header(header_prefix + extra_header)
    
    # Read payload
    payload = read_bytes(header.payload_len)
    
    # Decrypt if needed
    if header.flags & FLAG_ENCRYPTED:
        if not password:
            raise ValueError("Password required to decrypt embedded data")
        key = derive_key(password, header.salt)
        aad = build_aad(header.flags, header.salt, header.nonce)
        plaintext = AESGCM(key).decrypt(header.nonce, payload, aad)
    else:
        plaintext = payload
    
    # Determine payload type and extract accordingly
    if header.flags & FLAG_PAYLOAD_IMAGE:
        # Extract image
        img_width = int.from_bytes(read_bytes(4), byteorder="big")
        img_height = int.from_bytes(read_bytes(4), byteorder="big")
        
        # Reconstruct image
        pixels = []
        for i in range(0, len(plaintext), 3):
            if i + 3 <= len(plaintext):
                pixels.append(tuple(plaintext[i:i+3]))
        
        image = Image.new("RGB", (img_width, img_height))
        image.putdata(pixels)
        image.save(output_path)
        logging.info("Extracted image from MP3: %s", output_path)
    else:
        # Extract text/file
        with open(output_path, "wb") as f:
            f.write(plaintext)
        logging.info("Extracted text/file from MP3: %s", output_path)


# Legacy functions for backward compatibility
def embed_image_in_mp3(mp3_path: str, image_path: str, output_path: str, password: str | None = None) -> None:
    """Legacy function - use embed_data_in_mp3 instead."""
    embed_data_in_mp3(mp3_path, output_path, password=password, image_path=image_path)


def extract_image_from_mp3(mp3_path: str, output_path: str, password: str | None = None) -> None:
    """Legacy function - use extract_data_from_mp3 instead."""
    extract_data_from_mp3(mp3_path, output_path, password=password)


def load_mp4(path: str) -> None:
    """Load and validate MP4 file exists."""
    try:
        with open(path, "rb") as f:
            pass
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"MP4 file not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Could not open MP4 file '{path}': {exc}") from exc


def embed_data_in_mp4(mp4_path: str, output_path: str, password: str | None = None,
                      message: str | None = None, in_file: str | None = None,
                      image_path: str | None = None, mp3_path: str | None = None) -> None:
    """Embed text/file data, image, or MP3 into an MP4 file using metadata with optional encryption."""
    import shutil
    
    load_mp4(mp4_path)
    
    # Determine payload type
    payload_count = sum([message is not None, in_file is not None, image_path is not None, mp3_path is not None])
    if payload_count == 0:
        raise ValueError("Provide --message, --in-file, --image, or --mp3")
    if payload_count > 1:
        raise ValueError("Provide only one of: --message, --in-file, --image, or --mp3")
    
    flags = 0
    salt = b""
    nonce = b""
    plaintext = b""
    metadata = b""  # Additional metadata after payload
    
    if image_path:
        # Handle image embedding
        flags |= FLAG_PAYLOAD_IMAGE
        image = load_image(image_path)
        
        # Convert image to bytes
        image_bytes = bytearray()
        for pixel in image.getdata():
            image_bytes.extend(pixel)
        plaintext = bytes(image_bytes)
        
        # Store image dimensions in metadata
        metadata = image.size[0].to_bytes(4, byteorder="big") + image.size[1].to_bytes(4, byteorder="big")
    elif mp3_path:
        # Handle MP3 embedding
        flags |= FLAG_PAYLOAD_MP3
        load_mp3(mp3_path)
        with open(mp3_path, "rb") as f:
            plaintext = f.read()
    else:
        # Handle text/file embedding
        flags |= FLAG_PAYLOAD_TEXT
        if message:
            plaintext = message.encode("utf-8")
        else:
            assert in_file is not None
            with open(in_file, "rb") as f:
                plaintext = f.read()
    
    # Encrypt (optional)
    payload_bytes = plaintext
    if password:
        flags |= FLAG_ENCRYPTED
        salt = os.urandom(DEFAULT_SALT_LEN)
        nonce = os.urandom(DEFAULT_NONCE_LEN)
        key = derive_key(password, salt)
        aad = build_aad(flags, salt, nonce)
        payload_bytes = AESGCM(key).encrypt(nonce, plaintext, aad)
    
    # Create header
    header = StegoHeader(flags=flags, salt=salt, nonce=nonce, payload_len=len(payload_bytes)).to_bytes()
    stego_data = header + payload_bytes + metadata
    
    # Load or create MP4 metadata
    try:
        tags = MP4(mp4_path)
    except:
        tags = MP4()
    
    # Store embedded data in custom metadata atom
    # MP4 uses base64-encoded strings for data storage (mutagen limitation)
    stego_b64 = base64.b64encode(stego_data).decode('ascii')
    tags["©stg"] = [stego_b64]
    
    # Save to output file
    shutil.copy(mp4_path, output_path)
    tags.save(output_path)
    
    payload_type_map = {
        FLAG_PAYLOAD_IMAGE: "image",
        FLAG_PAYLOAD_TEXT: "text/file",
        FLAG_PAYLOAD_MP3: "MP3 file"
    }
    payload_type = payload_type_map.get(flags & 0x38, "data")
    logging.info("Embedded %s in MP4: %s", payload_type, output_path)


def extract_data_from_mp4(mp4_path: str, output_path: str, password: str | None = None) -> None:
    """Extract text/file data, image, or MP3 from an MP4 file with optional decryption."""
    load_mp4(mp4_path)
    
    try:
        tags = MP4(mp4_path)
    except:
        raise ValueError("Could not read MP4 metadata")
    
    # Extract stego data from custom metadata atom
    if "©stg" not in tags:
        raise ValueError("No embedded data found in MP4 file")
    
    # Decode from base64 (mutagen stores as string)
    stego_b64 = tags["©stg"][0]
    stego_data = base64.b64decode(stego_b64)
    
    # Parse header
    cursor = 0
    
    def read_bytes(num_bytes: int) -> bytes:
        nonlocal cursor
        data = stego_data[cursor:cursor + num_bytes]
        cursor += num_bytes
        return data
    
    header_prefix = read_bytes(12)
    salt_len = header_prefix[6]
    nonce_len = header_prefix[7]
    
    extra_header = b""
    if salt_len + nonce_len > 0:
        extra_header = read_bytes(salt_len + nonce_len)
    
    header = parse_header(header_prefix + extra_header)
    
    # Read payload
    payload = read_bytes(header.payload_len)
    
    # Decrypt if needed
    if header.flags & FLAG_ENCRYPTED:
        if not password:
            raise ValueError("Password required to decrypt embedded data")
        key = derive_key(password, header.salt)
        aad = build_aad(header.flags, header.salt, header.nonce)
        plaintext = AESGCM(key).decrypt(header.nonce, payload, aad)
    else:
        plaintext = payload
    
    # Determine payload type and extract accordingly
    if header.flags & FLAG_PAYLOAD_IMAGE:
        # Extract image
        img_width = int.from_bytes(read_bytes(4), byteorder="big")
        img_height = int.from_bytes(read_bytes(4), byteorder="big")
        
        # Reconstruct image
        pixels = []
        for i in range(0, len(plaintext), 3):
            if i + 3 <= len(plaintext):
                pixels.append(tuple(plaintext[i:i+3]))
        
        image = Image.new("RGB", (img_width, img_height))
        image.putdata(pixels)
        image.save(output_path)
        logging.info("Extracted image from MP4: %s", output_path)
    elif header.flags & FLAG_PAYLOAD_MP3:
        # Extract MP3
        with open(output_path, "wb") as f:
            f.write(plaintext)
        logging.info("Extracted MP3 from MP4: %s", output_path)
    else:
        # Extract text/file
        with open(output_path, "wb") as f:
            f.write(plaintext)
        logging.info("Extracted text/file from MP4: %s", output_path)


def read_payload(message: str | None, infile: str | None) -> bytes:
    if message and infile:
        raise ValueError("Provide either --message or --in-file, not both")
    if not message and not infile:
        raise ValueError("A payload is required via --message or --in-file")

    if message:
        return message.encode("utf-8")

    assert infile is not None
    with open(infile, "rb") as f:
        return f.read()


def encode_image(args: argparse.Namespace) -> None:
    image = load_image(args.image)
    plaintext = read_payload(args.message, args.in_file)

    flags = 0
    salt = b""
    nonce = b""
    payload_bytes = plaintext

    # Encryption (optional, controlled by --password)
    if args.password:
        flags |= FLAG_ENCRYPTED
        salt = os.urandom(DEFAULT_SALT_LEN)
        nonce = os.urandom(DEFAULT_NONCE_LEN)
        key = derive_key(args.password, salt)
        aad = build_aad(flags, salt, nonce)
        payload_bytes = AESGCM(key).encrypt(nonce, plaintext, aad)

    # Method flags
    method = args.method
    if method == "lsb-prng":
        flags |= FLAG_PRNG
    elif method == "lsb-match-prng":
        flags |= (FLAG_PRNG | FLAG_LSB_MATCH)

    header = StegoHeader(flags=flags, salt=salt, nonce=nonce, payload_len=len(payload_bytes)).to_bytes()
    total_bytes = len(header) + len(payload_bytes)
    capacity = max_payload_bytes(image)
    if total_bytes > capacity:
        raise ValueError(
            f"Payload {total_bytes} bytes exceeds capacity {capacity} bytes; use a larger image"
        )

    bits = bytes_to_bits(header + payload_bytes)

    if method == "lsb":
        stego = embed_bits(image, bits)
    elif method in ("lsb-prng", "lsb-match-prng"):
        if not args.prng_key:
            raise ValueError("PRNG key required for method 'lsb-prng' or 'lsb-match-prng'")
        rng = make_rng(args.prng_key)
        stego = embed_bits_prng(image, bits, rng, lsb_match=(method == "lsb-match-prng"))
    else:
        raise ValueError(f"Unknown method: {method}")

    stego.save(args.out)
    logging.info("Wrote stego image to %s", args.out)


def decode_image(args: argparse.Namespace) -> None:
    image = load_image(args.image)
    # Choose extraction method based on CLI
    method = args.method
    channels_len = len(flatten_channels(image))
    if method == "lsb":
        all_bits = extract_bits(image, channels_len)
    elif method in ("lsb-prng", "lsb-match-prng"):
        if not args.prng_key:
            raise ValueError("PRNG key required for method 'lsb-prng' or 'lsb-match-prng'")
        rng = make_rng(args.prng_key)
        all_bits = extract_bits_prng(image, channels_len, rng)
    else:
        raise ValueError(f"Unknown method: {method}")

    cursor = 0

    def read_bytes_from_bits(num_bytes: int) -> bytes:
        nonlocal cursor
        bit_slice = all_bits[cursor : cursor + num_bytes * 8]
        if len(bit_slice) < num_bytes * 8:
            raise ValueError("Unexpected end of data while decoding")
        cursor += num_bytes * 8
        return bits_to_bytes(bit_slice)

    header_prefix = read_bytes_from_bits(12)
    salt_len = header_prefix[6]
    nonce_len = header_prefix[7]

    extra_header = b""
    extra_header_len = salt_len + nonce_len
    if extra_header_len:
        extra_header = read_bytes_from_bits(extra_header_len)

    header = parse_header(header_prefix + extra_header)

    remaining_bits = len(all_bits) - cursor
    required_bits = header.payload_len * 8
    if required_bits > remaining_bits:
        raise ValueError("Image does not contain the full payload length declared in header")

    payload_bits = all_bits[cursor : cursor + required_bits]
    payload = bits_to_bytes(payload_bits)

    if header.flags & FLAG_ENCRYPTED:
        if not args.password:
            raise ValueError("Password required to decrypt payload")
        key = derive_key(args.password, header.salt)
        aad = build_aad(header.flags, header.salt, header.nonce)
        plaintext = AESGCM(key).decrypt(header.nonce, payload, aad)
    else:
        plaintext = payload

    if args.out:
        with open(args.out, "wb") as f:
            f.write(plaintext)
        logging.info("Wrote decoded payload to %s", args.out)
    else:
        try:
            decoded_text = plaintext.decode("utf-8")
        except UnicodeDecodeError:
            decoded_text = plaintext.decode("utf-8", errors="replace")
        print(decoded_text)


def encode_mp3(args: argparse.Namespace) -> None:
    """Encode text/file data or image into an MP3 file."""
    embed_data_in_mp3(
        args.mp3,
        args.out,
        password=args.password,
        message=getattr(args, 'message', None),
        in_file=getattr(args, 'in_file', None),
        image_path=getattr(args, 'image', None)
    )


def decode_mp3(args: argparse.Namespace) -> None:
    """Decode text/file data or image from an MP3 file."""
    extract_data_from_mp3(args.mp3, args.out, password=args.password)


def encode_mp4(args: argparse.Namespace) -> None:
    """Encode text/file data, image, or MP3 into an MP4 file."""
    embed_data_in_mp4(
        args.mp4,
        args.out,
        password=args.password,
        message=getattr(args, 'message', None),
        in_file=getattr(args, 'in_file', None),
        image_path=getattr(args, 'image', None),
        mp3_path=getattr(args, 'mp3', None)
    )


def decode_mp4(args: argparse.Namespace) -> None:
    """Decode text/file data, image, or MP3 from an MP4 file."""
    extract_data_from_mp4(args.mp4, args.out, password=args.password)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LSB image steganography, MP3/MP4 audio/video embedding")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", required=True)

    enc = subparsers.add_parser("encode", help="Embed data into an image")
    enc.add_argument("--image", required=True, help="Input cover image path")
    enc.add_argument("--out", required=True, help="Output stego image path")
    enc.add_argument("--message", help="Plaintext message to embed")
    enc.add_argument("--in-file", help="File whose contents to embed")
    enc.add_argument("--password", help="Password for AES-256-GCM encryption")
    enc.add_argument(
        "--method",
        choices=["lsb", "lsb-prng", "lsb-match-prng"],
        default="lsb",
        help="Embedding method (default: lsb)",
    )
    enc.add_argument(
        "--prng-key",
        help="Key string to seed PRNG embedding (required for prng methods)",
    )
    enc.set_defaults(func=encode_image)

    dec = subparsers.add_parser("decode", help="Extract data from an image")
    dec.add_argument("--image", required=True, help="Stego image path")
    dec.add_argument("--password", help="Password if payload is encrypted")
    dec.add_argument("--out", help="Write decoded payload to file instead of stdout")
    dec.add_argument(
        "--method",
        choices=["lsb", "lsb-prng", "lsb-match-prng"],
        default="lsb",
        help="Decoding method used for embedding",
    )
    dec.add_argument(
        "--prng-key",
        help="PRNG key string if embedding used PRNG",
    )
    dec.set_defaults(func=decode_image)

    # MP3 encoding subcommand
    mp3_enc = subparsers.add_parser("mp3-encode", help="Embed text/file data or image into an MP3 file")
    mp3_enc.add_argument("--mp3", required=True, help="Input MP3 file path")
    mp3_enc.add_argument("--out", required=True, help="Output MP3 file path")
    mp3_enc.add_argument("--image", help="Image file to embed")
    mp3_enc.add_argument("--message", help="Plaintext message to embed")
    mp3_enc.add_argument("--in-file", help="File whose contents to embed")
    mp3_enc.add_argument("--password", help="Password for AES-256-GCM encryption")
    mp3_enc.set_defaults(func=encode_mp3)

    # MP3 decoding subcommand
    mp3_dec = subparsers.add_parser("mp3-decode", help="Extract text/file data or image from an MP3 file")
    mp3_dec.add_argument("--mp3", required=True, help="MP3 file with embedded data")
    mp3_dec.add_argument("--out", required=True, help="Output file path (image or text/file)")
    mp3_dec.add_argument("--password", help="Password if data is encrypted")
    mp3_dec.set_defaults(func=decode_mp3)

    # MP4 encoding subcommand
    mp4_enc = subparsers.add_parser("mp4-encode", help="Embed text/file data, image, or MP3 into an MP4 file")
    mp4_enc.add_argument("--mp4", required=True, help="Input MP4 file path")
    mp4_enc.add_argument("--out", required=True, help="Output MP4 file path")
    mp4_enc.add_argument("--image", help="Image file to embed")
    mp4_enc.add_argument("--message", help="Plaintext message to embed")
    mp4_enc.add_argument("--in-file", help="File whose contents to embed")
    mp4_enc.add_argument("--mp3", help="MP3 file to embed")
    mp4_enc.add_argument("--password", help="Password for AES-256-GCM encryption")
    mp4_enc.set_defaults(func=encode_mp4)

    # MP4 decoding subcommand
    mp4_dec = subparsers.add_parser("mp4-decode", help="Extract text/file data, image, or MP3 from an MP4 file")
    mp4_dec.add_argument("--mp4", required=True, help="MP4 file with embedded data")
    mp4_dec.add_argument("--out", required=True, help="Output file path (image, text/file, or MP3)")
    mp4_dec.add_argument("--password", help="Password if data is encrypted")
    mp4_dec.set_defaults(func=decode_mp4)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        logging.error("%s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()