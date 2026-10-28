"""Esquemas de configuración del negocio."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class PublicSettingsOut(BaseModel):
    """Datos visibles en la web pública (sin información interna)."""

    brand_name: str
    brand_descriptor: str
    tagline: str
    logo_path: str | None = None
    phone: str
    whatsapp: str
    whatsapp_is_demo: bool
    email: EmailStr
    address_line: str
    city: str
    office_hours: str
    instagram: str | None = None
    facebook: str | None = None
    linkedin: str | None = None
    institutional_text: str
    footer_note: str
    developer_credit: str
    default_currency: Literal["ARS", "USD", "EUR"]
    show_expenses: bool

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    """Actualización desde el panel (sólo rol admin)."""

    brand_name: str | None = Field(default=None, min_length=2, max_length=120)
    brand_descriptor: str | None = Field(default=None, max_length=60)
    tagline: str | None = Field(default=None, max_length=200)
    logo_path: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    whatsapp: str | None = Field(default=None, max_length=40)
    whatsapp_is_demo: bool | None = None
    email: EmailStr | None = None
    address_line: str | None = Field(default=None, max_length=180)
    city: str | None = Field(default=None, max_length=120)
    office_hours: str | None = Field(default=None, max_length=120)
    instagram: str | None = Field(default=None, max_length=160)
    facebook: str | None = Field(default=None, max_length=160)
    linkedin: str | None = Field(default=None, max_length=160)
    institutional_text: str | None = Field(default=None, max_length=2000)
    footer_note: str | None = Field(default=None, max_length=400)
    default_currency: Literal["ARS", "USD", "EUR"] | None = None
    show_expenses: bool | None = None

    @field_validator("whatsapp")
    @classmethod
    def _clean_whatsapp(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = "".join(ch for ch in value if ch.isdigit())
        return cleaned or None

    @field_validator("brand_name", "tagline", "institutional_text", "footer_note")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class SettingsAdminOut(PublicSettingsOut):
    id: int
    created_at: datetime
    updated_at: datetime
