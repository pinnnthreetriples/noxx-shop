"""Encrypt admin TOTP secrets at rest, with a no-lockout fallback.

If ADMIN_TOTP_ENC_KEY is unset, both functions are no-ops (plaintext,
today's behavior). If it's set, new secrets are encrypted (prefixed
"fernet:"); existing legacy plaintext secrets still decrypt (returned
as-is) so setting the key can never lock out an already-enrolled admin.
"""
from cryptography.fernet import Fernet

from app.core.config import settings

_PREFIX = "fernet:"


def encrypt_secret(plaintext: str) -> str:
    if not settings.admin_totp_enc_key:
        return plaintext
    token = Fernet(settings.admin_totp_enc_key).encrypt(plaintext.encode()).decode()
    return _PREFIX + token


def decrypt_secret(stored: str) -> str:
    if not stored or not stored.startswith(_PREFIX):
        return stored
    if not settings.admin_totp_enc_key:
        return stored
    token = stored[len(_PREFIX):]
    return Fernet(settings.admin_totp_enc_key).decrypt(token.encode()).decode()
