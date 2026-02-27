"""Fernet symmetric encryption for sensitive data."""

import base64
import logging

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Lazy-init Fernet from ENCRYPTION_KEY or derive from SECRET_KEY."""
    global _fernet
    if _fernet is not None:
        return _fernet
    key = settings.ENCRYPTION_KEY
    if key:
        try:
            _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logger.warning("Invalid ENCRYPTION_KEY, deriving from SECRET_KEY: %s", e)
            key = None
    if not key:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"paritycheck",
            iterations=100000,
        )
        derived = base64.urlsafe_b64encode(
            kdf.derive(settings.SECRET_KEY.encode())
        )
        _fernet = Fernet(derived)
    return _fernet


def encrypt(value: str) -> str:
    """Encrypt a string; returns base64-encoded ciphertext."""
    if not value:
        return ""
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Decrypt a base64-encoded ciphertext; returns plaintext."""
    if not value:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(value.encode()).decode()
    except InvalidToken:
        logger.warning("Decryption failed: invalid token")
        return ""


def decrypt_optional(value: str | None) -> str:
    """Decrypt or return empty string if None."""
    return decrypt(value) if value else ""
