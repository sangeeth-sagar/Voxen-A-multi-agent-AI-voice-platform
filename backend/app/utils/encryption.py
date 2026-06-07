"""
Fernet-based symmetric encryption for per-user API keys at rest.

The secret is read from `settings.ENCRYPTION_KEY` (Fernet URL-safe base64
key, 32 bytes). Generate one with:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings


_cipher: Fernet | None = None


def _get_cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        if not settings.encryption_key:
            raise RuntimeError(
                "ENCRYPTION_KEY is not configured. Set it in your .env file."
            )
        _cipher = Fernet(settings.encryption_key.encode())
    return _cipher


def encrypt_key(plain_text: str) -> str:
    """Encrypt a plaintext API key. Returns URL-safe base64 ciphertext."""
    return _get_cipher().encrypt(plain_text.encode()).decode()


def decrypt_key(encrypted_text: str) -> str:
    """Decrypt a Fernet-encrypted API key back to plaintext."""
    try:
        return _get_cipher().decrypt(encrypted_text.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Stored key is invalid or was encrypted with a different key") from exc
