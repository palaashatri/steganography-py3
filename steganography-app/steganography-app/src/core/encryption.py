import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

class EncryptionManager:
    def __init__(self):
        self.backend = default_backend()
    
    def encrypt(self, data: bytes, password: str, method: str = "AES-256") -> bytes:
        if method == "AES-256":
            return self._encrypt_aes(data, password)
        elif method == "ChaCha20":
            return self._encrypt_chacha20(data, password)
        elif method == "Fernet":
            return self._encrypt_fernet(data, password)
        else:
            raise ValueError(f"Unsupported encryption method: {method}")
    
    def decrypt(self, encrypted_data: bytes, password: str, method: str = "AES-256") -> bytes:
        if method == "AES-256":
            return self._decrypt_aes(encrypted_data, password)
        elif method == "ChaCha20":
            return self._decrypt_chacha20(encrypted_data, password)
        elif method == "Fernet":
            return self._decrypt_fernet(encrypted_data, password)
        else:
            raise ValueError(f"Unsupported decryption method: {method}")
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(password.encode())
    
    def _encrypt_aes(self, data: bytes, password: str) -> bytes:
        salt = os.urandom(16)
        iv = os.urandom(16)
        key = self._derive_key(password, salt)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        padded_data = self._pad_data(data)
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return salt + iv + encrypted_data
    
    def _decrypt_aes(self, encrypted_data: bytes, password: str) -> bytes:
        salt = encrypted_data[:16]
        iv = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        
        key = self._derive_key(password, salt)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        return self._unpad_data(padded_data)
    
    def _encrypt_chacha20(self, data: bytes, password: str) -> bytes:
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = self._derive_key(password, salt)
        
        cipher = Cipher(algorithms.ChaCha20(key, nonce), None, backend=self.backend)
        encryptor = cipher.encryptor()
        
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        return salt + nonce + encrypted_data
    
    def _decrypt_chacha20(self, encrypted_data: bytes, password: str) -> bytes:
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]
        
        key = self._derive_key(password, salt)
        
        cipher = Cipher(algorithms.ChaCha20(key, nonce), None, backend=self.backend)
        decryptor = cipher.decryptor()
        
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def _encrypt_fernet(self, data: bytes, password: str) -> bytes:
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        fernet_key = base64.urlsafe_b64encode(key)
        
        fernet = Fernet(fernet_key)
        encrypted_data = fernet.encrypt(data)
        
        return salt + encrypted_data
    
    def _decrypt_fernet(self, encrypted_data: bytes, password: str) -> bytes:
        salt = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        key = self._derive_key(password, salt)
        fernet_key = base64.urlsafe_b64encode(key)
        
        fernet = Fernet(fernet_key)
        return fernet.decrypt(ciphertext)
    
    def _pad_data(self, data: bytes) -> bytes:
        padding_length = 16 - (len(data) % 16)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, padded_data: bytes) -> bytes:
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]
    
    def generate_key(self) -> str:
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

class Encryption:
    def __init__(self, password: str):
        self.key = self.derive_key(password)

    def derive_key(self, password: str) -> bytes:
        # Derive a key from the given password using SHA-256
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return base64.urlsafe_b64encode(key + salt)

    def encrypt(self, data: bytes) -> bytes:
        fernet = Fernet(self.key)
        return fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        fernet = Fernet(self.key)
        return fernet.decrypt(token)

    def save_key(self, file_path: str):
        with open(file_path, 'wb') as key_file:
            key_file.write(self.key)

    def load_key(self, file_path: str):
        with open(file_path, 'rb') as key_file:
            self.key = key_file.read()