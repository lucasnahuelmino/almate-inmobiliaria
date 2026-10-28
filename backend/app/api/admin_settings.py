"""Configuración del negocio (panel)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_staff
from app.database import get_db
from app.models.settings import DEFAULT_CREDIT, BusinessSettings
from app.models.user import User
from app.schemas.settings import SettingsAdminOut, SettingsUpdate

router = APIRouter(prefix="/admin", tags=["Admin · Configuración"])


@router.get(
    "/settings",
    response_model=SettingsAdminOut,
    summary="Leer configuración del negocio (cualquier rol)",
)
def get_settings_admin(
    db: Session = Depends(get_db), _: User = Depends(require_staff)
) -> SettingsAdminOut:
    return SettingsAdminOut.model_validate(BusinessSettings.get_or_create(db))


@router.put(
    "/settings",
    response_model=SettingsAdminOut,
    summary="Actualizar configuración (sólo rol admin)",
)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SettingsAdminOut:
    settings = BusinessSettings.get_or_create(db)
    data = payload.model_dump(exclude_unset=True)

    # El crédito de ALMATE Digital Studio no es editable: forma parte de la demo.
    data.pop("developer_credit", None)

    for field, value in data.items():
        if field == "email" and value is not None:
            value = str(value).strip().lower()
        if isinstance(value, str):
            value = value.strip() or getattr(settings, field)
        setattr(settings, field, value)

    settings.developer_credit = DEFAULT_CREDIT

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return SettingsAdminOut.model_validate(settings)
