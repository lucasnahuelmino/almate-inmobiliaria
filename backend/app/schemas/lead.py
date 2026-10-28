"""Esquemas de consultas, tasaciones, publicaciones y notas internas."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.lead import InquiryKind, LeadStatus

PHONE_PATTERN = re.compile(r"^[0-9\s()+.\-]{5,40}$")


def _validate_phone(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not PHONE_PATTERN.match(value):
        raise ValueError("El teléfono sólo puede contener números, espacios y + ( ) . -")
    return value


class InquiryCreate(BaseModel):
    """Consulta enviada por el formulario de contacto o desde una ficha."""

    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    message: str = Field(min_length=10, max_length=3000)
    property_code: str | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("Ingresá tu nombre.")
        return value

    @field_validator("message")
    @classmethod
    def _clean_message(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return _validate_phone(value)


class ValuationRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    property_type: str = Field(min_length=3, max_length=60)
    operation: str | None = Field(default=None, max_length=40)
    locality: str = Field(min_length=2, max_length=120)
    neighborhood: str | None = Field(default=None, max_length=120)
    surface_covered: str | None = Field(default=None, max_length=30)
    bedrooms: str | None = Field(default=None, max_length=10)
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return _validate_phone(value)


class ListingRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    operation: str = Field(min_length=3, max_length=40)
    property_type: str = Field(min_length=3, max_length=60)
    locality: str = Field(min_length=2, max_length=120)
    neighborhood: str | None = Field(default=None, max_length=120)
    surface_covered: str | None = Field(default=None, max_length=30)
    bedrooms: str | None = Field(default=None, max_length=10)
    expected_price: str | None = Field(default=None, max_length=40)
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        return _validate_phone(value)


# ---------------------------------------------------------------------------
# Salidas (panel)
# ---------------------------------------------------------------------------
class NoteOut(BaseModel):
    id: int
    body: str
    author_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InquiryOut(BaseModel):
    id: int
    kind: InquiryKind
    status: LeadStatus
    name: str
    email: str
    phone: str | None = None
    message: str
    property_id: str | None = None
    property_code: str | None = None
    property_title: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    notes: list[NoteOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ValuationRequestOut(BaseModel):
    id: int
    status: LeadStatus
    name: str
    email: str
    phone: str | None = None
    property_type: str
    operation: str | None = None
    locality: str
    neighborhood: str | None = None
    surface_covered: str | None = None
    bedrooms: str | None = None
    message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    notes: list[NoteOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ListingRequestOut(BaseModel):
    id: int
    status: LeadStatus
    name: str
    email: str
    phone: str | None = None
    operation: str
    property_type: str
    locality: str
    neighborhood: str | None = None
    surface_covered: str | None = None
    bedrooms: str | None = None
    expected_price: str | None = None
    message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    notes: list[NoteOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class NoteCreate(BaseModel):
    body: str = Field(min_length=2, max_length=2000)

    @field_validator("body")
    @classmethod
    def _clean(cls, value: str) -> str:
        return value.strip()


class AcceptedResponse(BaseModel):
    """Respuesta estándar de los formularios públicos."""

    ok: bool = True
    message: str
    id: int
