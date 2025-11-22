"""
CCC Stage 2 - Encryption Service
Version: 1.0
Author: Phase 2 Implementation
"""

import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.enabled = os.getenv('CCC_ENCRYPTION_ENABLED', 'false').lower() == 'true'
        self.fernet = None
        
        if self.enabled:
            if encryption_key:
                self.fernet = Fernet(encryption_key.encode())
            else:
                # Generate key from environment or create default
                key = self._get_or_create_key()
                self.fernet = Fernet(key)
        else:
            logger.info("Encryption disabled for development")
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate one"""
        env_key = os.getenv('CCC_ENCRYPTION_KEY')

        if env_key:
            # Use provided key with installation-specific salt
            # Generate salt from a combination of environment and machine info
            import hashlib
            salt_source = f"{env_key[:8]}{os.path.abspath('.')}"
            salt = hashlib.sha256(salt_source.encode()).digest()[:16]

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(env_key.encode()))
            return key
        else:
            # Generate a key for development (not recommended for production)
            logger.warning("No encryption key provided, generating temporary key")
            return Fernet.generate_key()
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        if not self.enabled or not self.fernet:
            return data
        
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data  # Return original data if encryption fails
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        if not self.enabled or not self.fernet:
            return encrypted_data
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data  # Return encrypted data if decryption fails
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt sensitive fields in a dictionary"""
        if not self.enabled:
            return data
        
        # Define sensitive fields that should be encrypted
        sensitive_fields = ['content', 'directive', 'state_data', 'user_preferences']
        
        encrypted_data = data.copy()
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt sensitive fields in a dictionary"""
        if not self.enabled:
            return encrypted_data
        
        # Define sensitive fields that should be decrypted
        sensitive_fields = ['content', 'directive', 'state_data', 'user_preferences']
        
        decrypted_data = encrypted_data.copy()
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(str(decrypted_data[field]))
        
        return decrypted_data