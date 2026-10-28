"""Comprobación rápida de la API sin levantar un servidor HTTP.

Uso:  python scripts/smoke.py   (desde la carpeta backend/)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def check(label: str, fn) -> None:
    try:
        response = fn()
        content_type = response.headers.get("content-type", "")
        body = response.json() if content_type.startswith("application/json") else response.text
        print(f"[{response.status_code}] {label}: {str(body)[:200]}")
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {label}: {type(exc).__name__}: {exc}")


def main() -> int:
    with TestClient(app) as client:
        check("health", lambda: client.get("/api/health"))
        check("meta", lambda: client.get("/api/meta"))
        check("settings", lambda: client.get("/api/settings"))
        check("listado", lambda: client.get("/api/properties"))
        check("destacadas", lambda: client.get("/api/properties/featured"))
        check("detalle inexistente", lambda: client.get("/api/properties/ALM-XXXX-26"))
        check("admin sin token", lambda: client.get("/api/admin/properties"))
        check("login con credenciales malas", lambda: client.post(
            "/api/auth/login", json={"email": "no@existe.com", "password": "x"}
        ))
        check("consulta inválida", lambda: client.post(
            "/api/inquiries", json={"name": "T", "email": "no-email", "message": "x"}
        ))
        check("filtros inválidos", lambda: client.get(
            "/api/properties", params={"min_price": 100, "max_price": 50}
        ))
        check("openapi", lambda: client.get("/api/openapi.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
