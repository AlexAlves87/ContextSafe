"""
Field-level encryption utilities for sensitive persistence data.

Uses Fernet (symmetric encryption) from the cryptography library.
The encryption key is read from the CS_ENCRYPTION_KEY environment variable.
If the key is not set, encryption/decryption are no-ops (pass-through).

Traceability:
- Audit: B1
"""
from __future__ import annotations

import os

from cryptography.fernet import Fernet


_KEY = os.environ.get("CS_ENCRYPTION_KEY", "").encode()
_fernet = Fernet(_KEY) if _KEY else None


def encrypt(value: str | None) -> str | None:
    """Encrypt a string value using Fernet.

    Returns the original value if encryption is not configured
    or if the value is empty.
    """
    if _fernet and value:
        return _fernet.encrypt(value.encode()).decode()
    return value


def decrypt(value: str | None) -> str | None:
    """Decrypt a Fernet-encrypted string value.

    Returns the original value if encryption is not configured
    or if the value is empty.
    """
    if _fernet and value:
        return _fernet.decrypt(value.encode()).decode()
    return value
