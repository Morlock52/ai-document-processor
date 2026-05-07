from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings


@dataclass(frozen=True)
class WrappedSecret:
    nonce: bytes
    ciphertext: bytes


class CryptoError(RuntimeError):
    pass


def _master_key() -> bytes:
    raw = get_settings().studio_master_key
    if not raw:
        raise CryptoError(
            "STUDIO_MASTER_KEY is not set. Generate with: "
            "python -c \"import os, base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )
    try:
        key = base64.b64decode(raw)
    except Exception as exc:
        raise CryptoError("STUDIO_MASTER_KEY is not valid base64") from exc
    if len(key) != 32:
        raise CryptoError("STUDIO_MASTER_KEY must decode to exactly 32 bytes")
    return key


def wrap(plaintext: str, *, aad: bytes | None = None) -> WrappedSecret:
    """AES-256-GCM encrypt a vendor key. The auth tag is appended to ciphertext by AESGCM."""
    aes = AESGCM(_master_key())
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), aad)
    return WrappedSecret(nonce=nonce, ciphertext=ct)


def unwrap(wrapped: WrappedSecret, *, aad: bytes | None = None) -> str:
    aes = AESGCM(_master_key())
    pt = aes.decrypt(wrapped.nonce, wrapped.ciphertext, aad)
    return pt.decode("utf-8")


def fingerprint(plaintext: str) -> str:
    """Short non-reversible identifier for a vendor key, safe to log/show in UI."""
    import hashlib

    digest = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    return f"{digest[:4]}…{digest[-4:]}"
