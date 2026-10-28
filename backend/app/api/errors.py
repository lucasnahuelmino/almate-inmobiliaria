"""Errores y validaciones de la capa API."""

from __future__ import annotations

from fastapi import HTTPException
from pydantic import ValidationError

MAX_ERROR_DETAIL_ITEMS = 20


def validation_detail(exc_or_errors: ValidationError | list[dict]) -> list[dict]:
    """Convierte un `ValidationError` (o una lista de errores) en detalle HTTP legible."""
    errors = (
        exc_or_errors.errors()
        if hasattr(exc_or_errors, "errors")
        else list(exc_or_errors or [])
    )
    items: list[dict] = []
    for error in errors[:MAX_ERROR_DETAIL_ITEMS]:
        items.append(
            {
                "loc": [str(part) for part in error.get("loc", [])],
                "msg": error.get("msg", "Valor inválido."),
                "type": error.get("type", "value_error"),
            }
        )
    return items


def unprocessable(message: str, detail: list[dict] | None = None) -> HTTPException:
    """422 con mensaje comprensible y detalle por campo."""
    return HTTPException(
        status_code=422, detail={"message": message, "errors": detail or []}
    )
