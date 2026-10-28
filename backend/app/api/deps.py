"""Dependencias de autenticación y autorización del panel administrativo."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.security import TokenError, decode_access_token

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Token de acceso obtenido en POST /api/auth/login",
    auto_error=False,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resuelve el usuario a partir del token Bearer. 401 si es inválido."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Autenticación requerida."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "La sesión ya no es válida. Iniciá sesión nuevamente."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: UserRole):
    """Factory de dependencias: sólo permite los roles indicados (403 si no)."""

    allowed = set(roles)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "No tenés permisos para realizar esta acción."},
            )
        return user

    return dependency


# Acceso general al panel (admin o editor)
require_staff = require_roles(UserRole.ADMIN, UserRole.EDITOR)
# Acciones exclusivas del administrador (configuración, borrado definitivo)
require_admin = require_roles(UserRole.ADMIN)
