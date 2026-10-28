"""Consultas, solicitudes de tasación, solicitudes de publicación y notas internas.

Los datos de contacto son los únicos datos personales que la web pública envía.
Las notas internas jamás se exponen en la API pública.
"""

from __future__ import annotations

import enum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin, controlled_enum, utcnow


class LeadStatus(str, enum.Enum):
    """Estados comunes de una solicitud entrante."""

    NEW = "new"
    FOLLOWING = "following"
    ANSWERED = "answered"
    CLOSED = "closed"


class InquiryKind(str, enum.Enum):
    PROPERTY = "property"      # consulta sobre una propiedad publicada
    GENERAL = "general"        # consulta general / contacto


class Inquiry(Base, TimestampMixin):
    """Consulta enviada desde el formulario de contacto o desde una ficha."""

    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kind: Mapped[InquiryKind] = mapped_column(
        controlled_enum(InquiryKind), nullable=False, default=InquiryKind.GENERAL, index=True
    )
    property_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("properties.id", ondelete="SET NULL"), nullable=True, index=True
    )
    property_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    property_title: Mapped[str | None] = mapped_column(String(180), nullable=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[LeadStatus] = mapped_column(
        controlled_enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True
    )
    answered_at = mapped_column(DateTime, nullable=True)

    __table_args__ = (Index("ix_inquiries_status_created", "status", "created_at"),)

    notes: Mapped[list[InternalNote]] = relationship(
        back_populates="inquiry", cascade="all, delete-orphan", lazy="selectin"
    )


class ValuationRequest(Base, TimestampMixin):
    """Solicitud de tasación de una propiedad."""

    __tablename__ = "valuation_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    property_type: Mapped[str] = mapped_column(String(60), nullable=False)
    operation: Mapped[str | None] = mapped_column(String(40), nullable=True)
    locality: Mapped[str] = mapped_column(String(120), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(120), nullable=True)
    surface_covered: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bedrooms: Mapped[str | None] = mapped_column(String(10), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[LeadStatus] = mapped_column(
        controlled_enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True
    )

    __table_args__ = (Index("ix_valuation_status_created", "status", "created_at"),)

    notes: Mapped[list[InternalNote]] = relationship(
        back_populates="valuation", cascade="all, delete-orphan", lazy="selectin"
    )


class ListingRequest(Base, TimestampMixin):
    """Solicitud de publicación / oferta de una propiedad por un propietario."""

    __tablename__ = "listing_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    operation: Mapped[str] = mapped_column(String(40), nullable=False)
    property_type: Mapped[str] = mapped_column(String(60), nullable=False)
    locality: Mapped[str] = mapped_column(String(120), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(120), nullable=True)
    surface_covered: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bedrooms: Mapped[str | None] = mapped_column(String(10), nullable=True)
    expected_price: Mapped[str | None] = mapped_column(String(40), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[LeadStatus] = mapped_column(
        controlled_enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True
    )

    __table_args__ = (Index("ix_listing_status_created", "status", "created_at"),)

    notes: Mapped[list[InternalNote]] = relationship(
        back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )


class InternalNote(Base):
    """Nota administrativa. Visible sólo en el panel (nunca en la API pública)."""

    __tablename__ = "internal_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inquiry_id: Mapped[int | None] = mapped_column(
        ForeignKey("inquiries.id", ondelete="CASCADE"), nullable=True, index=True
    )
    valuation_id: Mapped[int | None] = mapped_column(
        ForeignKey("valuation_requests.id", ondelete="CASCADE"), nullable=True, index=True
    )
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listing_requests.id", ondelete="CASCADE"), nullable=True, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = mapped_column(DateTime, nullable=False, default=utcnow, index=True)

    inquiry: Mapped[Inquiry | None] = relationship(back_populates="notes")
    valuation: Mapped[ValuationRequest | None] = relationship(back_populates="notes")
    listing: Mapped[ListingRequest | None] = relationship(back_populates="notes")
