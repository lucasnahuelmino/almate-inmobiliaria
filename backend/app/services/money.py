"""Utilidades de importes y formatos."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def to_cents(value: Any) -> int | None:
    """Convierte un importe decimal (ej. 152000.50) a centavos enteros.

    Acepta `int`, `float`, `str` o `Decimal`. Devuelve `None` para valores nulos.
    Lanza `ValueError` si el importe no es válido o supera el máximo soportado.
    """
    if value is None or value == "":
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Importe inválido.") from exc
    if amount < 0:
        raise ValueError("El importe no puede ser negativo.")
    if amount >= Decimal("92233720368547758.07"):
        raise ValueError("El importe supera el máximo permitido.")
    cents = int((amount * 100).quantize(Decimal("1")))
    return cents


def from_cents(cents: int | None) -> Decimal | None:
    """Convierte centavos a decimal de dos posiciones para la API."""
    if cents is None:
        return None
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))


def normalise_decimal(value: Any) -> Decimal | None:
    """Normaliza superficies u otros decimales."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Valor numérico inválido.") from exc
