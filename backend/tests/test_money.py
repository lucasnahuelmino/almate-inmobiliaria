"""Pruebas de conversión y precisión de importes (centavos, no float)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.money import from_cents, normalise_decimal, to_cents


def test_to_cents_entero() -> None:
    assert to_cents(150000) == 15000000
    assert to_cents(0) == 0


def test_to_cents_decimal() -> None:
    assert to_cents("152000.50") == 15200050
    assert to_cents(Decimal("75000.55")) == 7500055
    assert to_cents("19.99") == 1999


def test_to_cents_un_decimal() -> None:
    assert to_cents("0.01") == 1
    assert to_cents("0.1") == 10


def test_to_cents_nulos() -> None:
    assert to_cents(None) is None
    assert to_cents("") is None


def test_to_cents_negativo_rechazado() -> None:
    with pytest.raises(ValueError):
        to_cents(-1)


def test_to_cents_invalido_rechazado() -> None:
    with pytest.raises(ValueError):
        to_cents("no-es-un-numero")


def test_to_cents_supera_el_maximo() -> None:
    with pytest.raises(ValueError):
        to_cents("99999999999999999")


def test_from_cents_dos_decimales() -> None:
    assert from_cents(15200050) == Decimal("152000.50")
    assert from_cents(1) == Decimal("0.01")
    assert from_cents(None) is None


def test_ida_y_vuelta_no_pierde_precision() -> None:
    original = Decimal("88550.25")
    assert from_cents(to_cents(original)) == original


def test_normalise_decimal() -> None:
    assert normalise_decimal("68.5") == Decimal("68.50")
    assert normalise_decimal(None) is None
    with pytest.raises(ValueError):
        normalise_decimal("x")
