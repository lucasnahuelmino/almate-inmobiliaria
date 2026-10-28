"""Seguridad y privacidad de la API pública y del panel."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import delete_property_record, make_property

# Endpoints administrativos que deben exigir token.
PROTECTED = [
    ("GET", "/api/admin/properties"),
    ("GET", "/api/admin/dashboard"),
    ("GET", "/api/admin/inquiries"),
    ("GET", "/api/admin/valuation-requests"),
    ("GET", "/api/admin/listing-requests"),
    ("GET", "/api/admin/settings"),
    ("GET", "/api/admin/uploads-limit"),
    ("POST", "/api/admin/properties"),
    ("POST", "/api/admin/properties/ALM-XXXX-99/status"),
    ("DELETE", "/api/admin/properties/ALM-XXXX-99"),
    ("GET", "/api/auth/me"),
]


def test_todos_los_endpoints_admin_piden_token(client: TestClient) -> None:
    for method, path in PROTECTED:
        response = client.request(method, path)
        assert response.status_code == 401, f"{method} {path} -> {response.status_code}"
        assert "message" in response.json()


def test_token_de_otra_aplicacion_rechazado(client: TestClient) -> None:
    headers = {"Authorization": "Bearer alquila-un-jwt-de-otro-lado"}
    assert client.get("/api/admin/properties", headers=headers).status_code == 401


def test_borradores_y_archivados_invisibles_para_el_publico(
    client: TestClient,
) -> None:
    draft = make_property(
        code="ALM-SEG-01", title="Borrador reservado", publication_status="draft"
    )
    archived = make_property(
        code="ALM-SEG-02", title="Archivado reservado", publication_status="archived"
    )
    try:
        assert client.get(f"/api/properties/{draft.code}").status_code == 404
        assert client.get(f"/api/properties/{archived.code}").status_code == 404

        listing = client.get(
            "/api/properties", params={"q": "reservado", "page_size": 60}
        ).json()
        codes = {item["code"] for item in listing["items"]}
        assert draft.code not in codes
        assert archived.code not in codes
    finally:
        delete_property_record(draft.code)
        delete_property_record(archived.code)


def test_direccion_no_publicada_se_omite(client: TestClient) -> None:
    prop = make_property(
        code="ALM-SEG-03",
        title="Propiedad con dirección privada",
        address="Calle Secreta 123",
        address_is_public=False,
    )
    try:
        body = client.get(f"/api/properties/{prop.code}").json()
        assert body["address"] is None
        assert body["address_is_public"] is False
    finally:
        delete_property_record("ALM-SEG-03")


def test_respuestas_publicas_sin_datos_sensibles(client: TestClient) -> None:
    for path in ("/api/properties", "/api/settings", "/api/meta"):
        text = client.get(path).text.lower()
        for forbidden in ("password", "password_hash", "secret", "jwt", "internalnote"):
            assert forbidden not in text, f"{path} expone '{forbidden}'"


def test_configuracion_publica_sin_campos_internos(
    client: TestClient, admin_headers
) -> None:
    public = client.get("/api/settings").json()
    admin = client.get("/api/admin/settings", headers=admin_headers).json()
    # El panel agrega metadatos internos; el público no los recibe.
    assert "id" in admin and "id" not in public
    assert "updated_at" in admin and "updated_at" not in public


def test_listado_admin_incluye_pero_publico_no(client: TestClient, admin_headers) -> None:
    prop = make_property(
        code="ALM-SEG-04", title="Borrador solo visible en panel", publication_status="draft"
    )
    try:
        admin_list = client.get(
            "/api/admin/properties", params={"q": "BORRADOR SOLO VISIBLE"}, headers=admin_headers
        ).json()
        assert any(item["code"] == prop.code for item in admin_list["items"])

        public_list = client.get(
            "/api/properties", params={"q": "BORRADOR SOLO VISIBLE"}
        ).json()
        assert public_list["total"] == 0
    finally:
        delete_property_record("ALM-SEG-04")


def test_editor_no_puede_borrar_ni_configurar(
    client: TestClient, editor_headers
) -> None:
    assert (
        client.delete("/api/admin/properties/ALM-XXXX-99", headers=editor_headers).status_code
        == 403
    )
    assert (
        client.put("/api/admin/settings", json={"phone": "+54 11 1"}, headers=editor_headers).status_code
        == 403
    )


def test_cors_solo_para_origenes_configurados(client: TestClient) -> None:
    allowed = client.get(
        "/api/health", headers={"Origin": "http://localhost:5173"}
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    foreign = client.get(
        "/api/health", headers={"Origin": "https://ejemplo-malicioso.com"}
    )
    assert foreign.headers.get("access-control-allow-origin") is None
