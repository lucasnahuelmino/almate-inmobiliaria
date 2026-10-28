"""Tipos y auxiliares compartidos por los modelos."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """Fecha/hora actual con zona horaria (en BD se guarda naive UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def controlled_enum(enum_cls: type[enum.Enum], length: int = 32) -> SAEnum:
    """Enum portable: se guarda el *valor* como VARCHAR (SQLite y PostgreSQL)."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        validate_strings=True,
        values_callable=lambda cls: [member.value for member in cls],
    )


class TimestampMixin:
    """created_at / updated_at gestionados por la aplicación (portable)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )


class CodeTypes:
    """Longitudes estándar de cadenas."""

    EMAIL = String(255)
    SHORT_TEXT = String(120)
    TITLE = String(180)
