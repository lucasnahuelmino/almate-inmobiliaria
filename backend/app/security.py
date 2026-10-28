"""Seguridad: hash de contraseñas (bcrypt) y tokens JWT (HS256)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

# bcrypt trunca a 72 bytes: se valida antes para evitar sorpresas silenciosas.
MAX_PASSWORD_BYTES = 72
BCRYPT_ROUNDS = 12


class TokenError(Exception):
    """Token inválido, expirado o con formato incorrecto."""


def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de la contraseña."""
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"La contraseña no puede superar los {MAX_PASSWORD_BYTES} bytes.")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Compara en claro con el hash almacenado (en tiempo constante)."""
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Firma un token JWT con expiración configurable."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": subject, "type": "access", "iat": datetime.now(timezone.utc), "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida el token. Lanza `TokenError` si no es válido."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:  # expirado, firma inválida, formato incorrecto
        raise TokenError("Token inválido o expirado.") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise TokenError("Token inválido.")
    return payload
