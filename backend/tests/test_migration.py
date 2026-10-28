"""La migración de Alembic debe poder aplicarse desde cero."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_head_desde_cero(tmp_path) -> None:
    """`alembic upgrade head` crea el esquema completo en una base nueva."""
    database = tmp_path / "migracion.db"
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{database.as_posix()}"
    env.setdefault("SECRET_KEY", "clave-de-prueba-para-migraciones-0123456789")

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    assert database.exists()
    connection = sqlite3.connect(database)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        connection.close()

    assert {
        "alembic_version",
        "users",
        "properties",
        "property_images",
        "inquiries",
        "valuation_requests",
        "listing_requests",
        "business_settings",
        "internal_notes",
    } <= tables


def test_migracion_es_repetible(tmp_path) -> None:
    """Volver a ejecutar `upgrade head` no debe fallar ni duplicar tablas."""
    database = tmp_path / "repetible.db"
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{database.as_posix()}"

    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, result.stderr
