"""
Encryption utilities for storing upstream API keys
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Master key from environment - this encrypts upstream API keys
MASTER_KEY = os.getenv("STREAMFIX_MASTER_KEY", "dev-key-change-in-production")


def _get_fernet():
    """Get Fernet cipher instance"""
    # Derive key from master key
    salt = b"streamfix_salt_v1"  # Fixed salt for deterministic key derivation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(MASTER_KEY.encode()))
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an upstream API key for storage"""
    f = _get_fernet()
    encrypted = f.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an upstream API key"""
    f = _get_fernet()
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted.decode()