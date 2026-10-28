"""Router de autenticación del panel administrativo."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.security import create_access_token, verify_password
from app.services.ratelimit import login_limiter
from app.models.common import utcnow

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión en el panel administrativo",
)
def login(
    payload: LoginRequest, request: Request, db: Session = Depends(get_db)
) -> TokenResponse:
    """Valida credenciales contra la base de datos y emite un token JWT.

    El mensaje de error es idéntico tanto si el usuario no existe como si la
    contraseña es incorrecta, para no revelar cuentas existentes.
    """
    login_limiter.check(login_limiter.client_key(request, "login"))

    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if user is None or not user.is_active or not verify_password(
        payload.password, user.password_hash or ""
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Credenciales inválidas."},
        )

    user.last_login_at = utcnow()
    db.add(user)
    db.commit()

    settings = get_settings()
    token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "name": user.full_name},
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut, summary="Usuario autenticado actual")
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
