import base64
import logging
import secrets
import time

import bcrypt
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi import HTTPException
from pydantic import BaseModel

from agent.config import settings

logger = logging.getLogger(__name__)

# ---- bcrypt ----


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---- RSA key pair (lazy generation) ----
_private_key: rsa.RSAPrivateKey | None = None
_public_key: rsa.RSAPublicKey | None = None


def _ensure_keys():
    global _private_key, _public_key
    if _private_key is None:
        _private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=settings.RSA_KEY_SIZE,
        )
        _public_key = _private_key.public_key()
        logger.info("RSA %d-bit key pair generated", settings.RSA_KEY_SIZE)


def get_public_key() -> str:
    _ensure_keys()
    return _public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


def decrypt_password(encrypted_b64: str) -> str:
    _ensure_keys()
    try:
        ciphertext = base64.b64decode(encrypted_b64)
        plaintext = _private_key.decrypt(ciphertext, padding.PKCS1v15())
        return plaintext.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Password decryption failed")


class TokenPair(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int


_jwt_secret: str | None = None
_JWT_SECRET_FILE = ".jwt_secret"


def _get_jwt_secret() -> str:
    global _jwt_secret
    if _jwt_secret is not None:
        return _jwt_secret
    key = settings.JWT_SECRET_KEY
    if key:
        _jwt_secret = key
        return _jwt_secret

    # 无配置时从文件读取或生成后持久化，确保重启后 token 仍有效
    import os
    # __file__ = src/core/security.py → 3 levels up = backend/
    secret_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        _JWT_SECRET_FILE)
    try:
        with open(secret_file) as f:
            _jwt_secret = f.read().strip()
        logger.info("Loaded JWT secret from %s", _JWT_SECRET_FILE)
    except FileNotFoundError:
        _jwt_secret = secrets.token_hex(32)
        with open(secret_file, "w") as f:
            f.write(_jwt_secret)
        logger.info("Generated persistent JWT secret → %s", _JWT_SECRET_FILE)

    return _jwt_secret


def create_token_pair(user_id: str) -> TokenPair:
    secret = _get_jwt_secret()
    now = int(time.time())
    access_payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + settings.JWT_ACCESS_EXPIRE,
    }
    refresh_payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + settings.JWT_REFRESH_EXPIRE,
    }
    return TokenPair(
        accessToken=jwt.encode(access_payload, secret, algorithm="HS256"),
        refreshToken=jwt.encode(refresh_payload, secret, algorithm="HS256"),
        expiresIn=settings.JWT_ACCESS_EXPIRE,
    )


def decode_token(token: str, expected_type: str = "access") -> dict:
    secret = _get_jwt_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token type")

    return payload


# ---- Fernet symmetric encryption for API keys ----

_fernet: Fernet | None = None
_FERNET_KEY_FILE = ".fernet_key"


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet

    key = settings.ENCRYPTION_KEY
    if key:
        _fernet = Fernet(key.encode())
        return _fernet

    import os
    key_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        _FERNET_KEY_FILE,
    )
    try:
        with open(key_path) as f:
            key = f.read().strip()
        _fernet = Fernet(key.encode())
        logger.info("Loaded encryption key from %s", _FERNET_KEY_FILE)
    except FileNotFoundError:
        key = Fernet.generate_key().decode()
        with open(key_path, "w") as f:
            f.write(key)
        _fernet = Fernet(key.encode())
        logger.info("Generated persistent encryption key → %s", _FERNET_KEY_FILE)

    return _fernet


def encrypt_api_key(plain: str) -> str:
    if not plain:
        return ""
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    if not encrypted:
        return ""
    return _get_fernet().decrypt(encrypted.encode()).decode()
