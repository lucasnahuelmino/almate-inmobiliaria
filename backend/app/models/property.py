"""Propiedades y fotografías.

Dos estados independientes (no confundirlos):

* `commercial_status`   → disponible, reservado, vendido, alquilado  (estado comercial)
* `publication_status`  → borrador, publicada, archivada            (estado de publicación)

El sitio público sólo muestra `publication_status == published`.

Los importes se almacenan en **centavos** (`*_cents`, BIGINT) para evitar
errores de punto flotante; la API los expone como decimales.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin, controlled_enum, utcnow


class Operation(str, enum.Enum):
    BUY = "buy"                      # comprar
    RENT = "rent"                    # alquilar
    TEMPORARY_RENT = "temporary_rent"  # alquiler temporal


class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    PH = "ph"
    LAND = "land"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    GARAGE = "garage"


class PriceUnit(str, enum.Enum):
    """Unidad en la que se expresa el importe."""

    TOTAL = "total"        # venta: importe total
    MONTHLY = "monthly"    # alquiler: por mes
    DAILY = "daily"        # alquiler temporal: por día


DEFAULT_UNIT_BY_OPERATION = {
    Operation.BUY: PriceUnit.TOTAL,
    Operation.RENT: PriceUnit.MONTHLY,
    Operation.TEMPORARY_RENT: PriceUnit.DAILY,
}


class CommercialStatus(str, enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    RENTED = "rented"


class PublicationStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Property(Base, TimestampMixin):
    __tablename__ = "properties"

    # --- Identidad -------------------------------------------------------
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Datos generales -------------------------------------------------
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    operation: Mapped[Operation] = mapped_column(
        controlled_enum(Operation), nullable=False, index=True
    )
    property_type: Mapped[PropertyType] = mapped_column(
        controlled_enum(PropertyType), nullable=False, index=True
    )
    is_development: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    price_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    price_unit: Mapped[PriceUnit] = mapped_column(
        controlled_enum(PriceUnit), nullable=False, default=PriceUnit.TOTAL
    )
    expenses_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    commercial_status: Mapped[CommercialStatus] = mapped_column(
        controlled_enum(CommercialStatus),
        nullable=False,
        default=CommercialStatus.AVAILABLE,
        index=True,
    )
    publication_status: Mapped[PublicationStatus] = mapped_column(
        controlled_enum(PublicationStatus),
        nullable=False,
        default=PublicationStatus.DRAFT,
        index=True,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # --- Ubicación -------------------------------------------------------
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="Argentina")
    province: Mapped[str] = mapped_column(String(80), nullable=False, default="Buenos Aires")
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)  # partido
    locality: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    neighborhood: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(180), nullable=True)
    # Si es False, la web pública sólo muestra localidad/barrio (dirección aproximada).
    address_is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- Características -------------------------------------------------
    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    toilets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    garages: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    antiquity_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    surface_covered: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    surface_semicovered: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    surface_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True, index=True)
    apto_professional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    services: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # --- Publicación -----------------------------------------------------
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    # --- Relaciones ------------------------------------------------------
    images: Mapped[list["PropertyImage"]] = relationship(
        back_populates="property_ref",
        cascade="all, delete-orphan",
        order_by="PropertyImage.sort_order",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_properties_publication_op", "publication_status", "operation"),
        Index("ix_properties_listing_sort", "publication_status", "published_at"),
        Index("ix_properties_status", "publication_status", "commercial_status"),
        Index("ix_properties_locality_type", "locality", "property_type"),
    )

    # --- Helpers ---------------------------------------------------------
    @property
    def is_available_for_public(self) -> bool:
        return self.publication_status == PublicationStatus.PUBLISHED

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Property {self.code} {self.title!r}>"


class PropertyImage(Base, TimestampMixin):
    __tablename__ = "property_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Ruta relativa al directorio estático, p. ej. uploads/properties/<id>/<uuid>.jpg
    storage_path: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(120), nullable=False)
    alt_text: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(60), nullable=False, default="image/jpeg")
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Nombre `property_ref` (y no `property`) para no pisar el decorador built-in.
    property_ref: Mapped[Property] = relationship(back_populates="images")

    __table_args__ = (
        Index("ix_property_images_order", "property_id", "sort_order"),
    )

    @property
    def url(self) -> str:
        """URL pública servida por FastAPI (`/static/...`)."""
        return f"/static/{self.storage_path.lstrip('/')}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PropertyImage {self.id} {self.filename} property={self.property_id}>"
