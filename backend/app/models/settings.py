"""Configuración del negocio (registro único, id = 1).

Permite personalizar la demo para otra inmobiliaria sin tocar código:
marca, colores heredados del frontend, contactos, WhatsApp, redes y textos.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import TimestampMixin

DEFAULT_CREDIT = "Sitio demo desarrollado por ALMATE · Digital Studio"


class BusinessSettings(Base, TimestampMixin):
    __tablename__ = "business_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # --- Identidad -------------------------------------------------------
    brand_name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="ALMATE Propiedades"
    )
    brand_descriptor: Mapped[str] = mapped_column(String(60), nullable=False, default="PROPIEDADES")
    tagline: Mapped[str] = mapped_column(
        String(200), nullable=False, default="Propiedades seleccionadas en el sur del Gran Buenos Aires"
    )
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Contacto --------------------------------------------------------
    phone: Mapped[str] = mapped_column(String(40), nullable=False, default="+54 9 11 5555-0000")
    # Número de demostración: sustituir por el de la inmobiliaria real.
    whatsapp: Mapped[str] = mapped_column(
        String(40), nullable=False, default="5491155550000"
    )
    whatsapp_is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email: Mapped[str] = mapped_column(
        String(120), nullable=False, default="hola@almatepropiedades.com.ar"
    )
    address_line: Mapped[str] = mapped_column(
        String(180), nullable=False, default="Av. Calchaquí 1234, Quilmes"
    )
    city: Mapped[str] = mapped_column(String(120), nullable=False, default="Quilmes, Buenos Aires")
    office_hours: Mapped[str] = mapped_column(
        String(120), nullable=False, default="Lunes a viernes de 9 a 18 hs · Sábados de 10 a 13 hs"
    )

    # --- Redes -----------------------------------------------------------
    instagram: Mapped[str | None] = mapped_column(String(160), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(160), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(160), nullable=True)

    # --- Textos ----------------------------------------------------------
    institutional_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=(
            "Acompañamos a compradores, inquilinos y propietarios con información clara, "
            "fotografías honestas y una gestión ordenada de principio a fin."
        ),
    )
    footer_note: Mapped[str] = mapped_column(
        Text, nullable=False, default="Valores y superficies de la demostración, no corresponden a precios reales de mercado."
    )
    developer_credit: Mapped[str] = mapped_column(
        String(200), nullable=False, default=DEFAULT_CREDIT
    )

    # --- Preferencias ----------------------------------------------------
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="ARS")
    show_expenses: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    @classmethod
    def get_or_create(cls, db) -> "BusinessSettings":
        """Devuelve el registro único, creándolo con valores por defecto."""
        settings = db.get(cls, 1)
        if settings is None:
            settings = cls(id=1)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
