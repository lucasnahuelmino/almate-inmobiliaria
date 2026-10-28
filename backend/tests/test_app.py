"""Pruebas de los endpoints transversales: salud, meta, configuración, errores."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"]


def test_version(client: TestClient) -> None:
    response = client.get("/api/version")
    assert response.status_code == 200
    assert response.json()["version"]


def test_meta_incluye_opciones_de_filtros(client: TestClient) -> None:
    body = client.get("/api/meta").json()
    operations = {item["value"] for item in body["operations"]}
    assert operations == {"buy", "rent", "temporary_rent"}
    assert all("label" in item for item in body["operations"])

    types = {item["value"] for item in body["property_types"]}
    assert {"apartment", "house", "ph", "land"} <= types

    assert set(body["currencies"]) >= {"ARS", "USD"}
    assert isinstance(body["localities"], list)
    assert {item["value"] for item in body["sort_options"]} >= {
        "recent",
        "price_asc",
        "price_desc",
    }


def test_settings_publicos(client: TestClient) -> None:
    body = client.get("/api/settings").json()
    assert body["brand_name"] == "ALMATE Propiedades"
    assert "ALMATE" in body["developer_credit"]
    assert body["whatsapp_is_demo"] is True
    assert body["default_currency"] in {"ARS", "USD", "EUR"}
    # Nunca debe filtrar datos internos (usuarios, tokens, notas).
    for forbidden in ("password", "token", "secret", "notes", "hash"):
        assert forbidden not in body


def test_openapi_disponible(client: TestClient) -> None:
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/properties" in schema["paths"]


def test_error_404_con_mensaje_legible(client: TestClient) -> None:
    response = client.get("/api/properties/ALM-NOEXISTE-99")
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"message"}
    assert body["message"]


def test_error_422_con_detalle_por_campo(client: TestClient) -> None:
    response = client.post(
        "/api/inquiries", json={"name": "A", "email": "no-es-correo", "message": "x"}
    )
    assert response.status_code == 422
    body = response.json()
    assert "message" in body
    assert isinstance(body["errors"], list)
    assert any(error.get("loc") for error in body["errors"])


def test_error_404_de_ruta_desconocida(client: TestClient) -> None:
    response = client.get("/api/esto-no-existe")
    assert response.status_code == 404
    assert "message" in response.json()


def test_cabeceras_de_seguridad(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_documentacion_marcada_como_no_indexable(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "noindex" in response.headers.get("X-Robots-Tag", "")


def test_health_verifica_laconexion_a_la_base(client: TestClient) -> None:
    # /api/health ejecuta `SELECT 1`: si la BD fallara devolvería 500.
    assert client.get("/api/health").status_code == 200
