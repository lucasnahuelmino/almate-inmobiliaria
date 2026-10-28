"""Esquemas de propiedades: listado público, detalle y administración.

Los importes viajan como decimales (`price`) y se almacenan en centavos.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.property import (
    CommercialStatus,
    Operation,
    PriceUnit,
    PropertyType,
    PublicationStatus,
)

Currency = Literal["ARS", "USD", "EUR"]
SortOption = Literal["recent", "oldest", "price_asc", "price_desc"]


# ---------------------------------------------------------------------------
# Imágenes
# ---------------------------------------------------------------------------
class PropertyImageOut(BaseModel):
    id: int
    url: str
    alt: str
    is_main: bool
    sort_order: int


class PropertyImageAdminOut(PropertyImageOut):
    filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Salida pública
# ---------------------------------------------------------------------------
class PropertySummaryOut(BaseModel):
    """Lo que necesita una tarjeta del catálogo."""

    code: str
    title: str
    operation: Operation
    property_type: PropertyType
    is_development: bool
    is_featured: bool
    price: Decimal | None
    currency: str
    price_unit: PriceUnit
    expenses: Decimal | None
    commercial_status: CommercialStatus
    publication_status: PublicationStatus

    country: str
    province: str
    department: str | None = None
    locality: str | None = None
    neighborhood: str | None = None
    address: str | None = None
    address_is_public: bool = True

    rooms: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    garages: int | None = None
    surface_covered: Decimal | None = None
    surface_total: Decimal | None = None
    apto_professional: bool = False

    published_at: datetime | None = None
    image: PropertyImageOut | None = None

    model_config = {"from_attributes": True}


class PropertyDetailOut(PropertySummaryOut):
    """Ficha completa de una propiedad publicada."""

    description: str
    toilets: int | None = None
    antiquity_years: int | None = None
    surface_semicovered: Decimal | None = None
    services: list[str] = Field(default_factory=list)
    images: list[PropertyImageOut] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Salida administrativa
# ---------------------------------------------------------------------------
class PropertyAdminOut(PropertyDetailOut):
    id: str
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
    images: list[PropertyImageAdminOut] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Escritura (alta y edición)
# ---------------------------------------------------------------------------
class PropertyBase(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    description: str = Field(default="", max_length=10000)
    operation: Operation
    property_type: PropertyType
    is_development: bool = False
    price: Decimal | None = Field(default=None, ge=0, le=Decimal("90000000000000000"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    # Si no se informa, se deriva de la operación (venta/por mes/por día).
    price_unit: PriceUnit | None = None
    expenses: Decimal | None = Field(default=None, ge=0, le=Decimal("90000000000000000"))
    commercial_status: CommercialStatus = CommercialStatus.AVAILABLE
    publication_status: PublicationStatus = PublicationStatus.DRAFT
    is_featured: bool = False

    country: str = Field(default="Argentina", max_length=80)
    province: str = Field(default="Buenos Aires", max_length=80)
    department: str | None = Field(default=None, max_length=120)
    locality: str | None = Field(default=None, max_length=120)
    neighborhood: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=180)
    address_is_public: bool = True

    rooms: int | None = Field(default=None, ge=0, le=50)
    bedrooms: int | None = Field(default=None, ge=0, le=50)
    bathrooms: int | None = Field(default=None, ge=0, le=50)
    toilets: int | None = Field(default=None, ge=0, le=50)
    garages: int | None = Field(default=None, ge=0, le=50)
    antiquity_years: int | None = Field(default=None, ge=0, le=500)
    surface_covered: Decimal | None = Field(default=None, ge=0, le=Decimal("10000000"))
    surface_semicovered: Decimal | None = Field(default=None, ge=0, le=Decimal("10000000"))
    surface_total: Decimal | None = Field(default=None, ge=0, le=Decimal("10000000"))
    apto_professional: bool = False
    services: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("currency")
    @classmethod
    def _currency_upper(cls, value: str) -> str:
        value = value.upper().strip()
        if not value.isalpha():
            raise ValueError("La moneda debe ser un código alfabético de 3 letras (ARS, USD…).")
        return value

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 5:
            raise ValueError("El título debe tener al menos 5 caracteres.")
        return value

    @field_validator("services")
    @classmethod
    def _clean_services(cls, value: list[str]) -> list[str]:
        cleaned = [" ".join(str(item).split()) for item in value if str(item).strip()]
        cleaned = [item[:60] for item in cleaned]
        if len(cleaned) > 30:
            raise ValueError("Máximo 30 servicios.")
        return cleaned

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str) -> str:
        return value.strip()


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(PropertyBase):
    """Edición: todos los campos son opcionales para permitir parches parciales."""

    title: str | None = Field(default=None, min_length=5, max_length=180)
    operation: Operation | None = None
    property_type: PropertyType | None = None
    country: str | None = Field(default=None, max_length=80)
    province: str | None = Field(default=None, max_length=80)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    commercial_status: CommercialStatus | None = None
    publication_status: PublicationStatus | None = None
    services: list[str] | None = Field(default=None, max_length=30)

    model_config = {"from_attributes": True}


class StatusUpdate(BaseModel):
    """Cambio puntual de estado comercial o de publicación."""

    publication_status: PublicationStatus | None = None
    commercial_status: CommercialStatus | None = None


# ---------------------------------------------------------------------------
# Filtros del catálogo público
# ---------------------------------------------------------------------------
class PublicFilters(BaseModel):
    operation: Operation | None = None
    type: PropertyType | None = None
    locality: str | None = None
    province: str | None = None
    q: str | None = Field(default=None, max_length=80)
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0, le=50)
    bathrooms: int | None = Field(default=None, ge=0, le=50)
    min_surface: Decimal | None = Field(default=None, ge=0)
    max_surface: Decimal | None = Field(default=None, ge=0)
    garage: bool | None = None
    apto_professional: bool | None = None
    development: bool | None = None
    featured: bool | None = None
    sort: SortOption = "recent"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=60)

    @model_validator(mode="after")
    def _check_prices(self) -> "PublicFilters":
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.max_price < self.min_price
        ):
            raise ValueError("El precio máximo no puede ser menor al mínimo.")
        if (
            self.min_surface is not None
            and self.max_surface is not None
            and self.max_surface < self.min_surface
        ):
            raise ValueError("La superficie máxima no puede ser menor a la mínima.")
        return self


class PropertyPage(BaseModel):
    items: list[PropertySummaryOut]
    total: int
    page: int
    page_size: int
    pages: int
