"""Formularios públicos: consultas, tasaciones y solicitudes de publicación."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import delete_property_record, make_property

VALID_INQUIRY = {
    "name": "Consulta de Interesado",
    "email": "interesado@ejemplo.com",
    "phone": "+54 11 5555-4444",
    "message": "Hola, quiero saber si se puede visitar el departamento.",
}

VALID_VALUATION = {
    "name": "Solicitante de Tasación",
    "email": "tasacion@ejemplo.com",
    "property_type": "house",
    "operation": "buy",
    "locality": "Bernal",
    "neighborhood": "Villa Antigua",
    "surface_covered": "110",
    "bedrooms": "3",
    "message": "Necesito tasar una casa para una venta.",
}

VALID_LISTING = {
    "name": "Propietario Ejemplar",
    "email": "propietario@ejemplo.com",
    "operation": "buy",
    "property_type": "apartment",
    "locality": "Quilmes",
    "surface_covered": "65",
    "bedrooms": "2",
    "expected_price": "USD 90.000",
    "message": "Quiero publicar mi departamento en el sitio.",
}


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------
def test_consulta_general_valida(client: TestClient) -> None:
    response = client.post("/api/inquiries", json=VALID_INQUIRY)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["message"]
    assert isinstance(body["id"], int)


def test_consulta_con_email_invalido(client: TestClient) -> None:
    payload = dict(VALID_INQUIRY, email="esto-no-es-un-correo")
    response = client.post("/api/inquiries", json=payload)
    assert response.status_code == 422
    assert response.json()["errors"]


def test_consulta_con_mensaje_corto(client: TestClient) -> None:
    payload = dict(VALID_INQUIRY, message="hola")
    response = client.post("/api/inquiries", json=payload)
    assert response.status_code == 422


def test_consulta_con_telefono_invalido(client: TestClient) -> None:
    payload = dict(VALID_INQUIRY, phone="no-telefono")
    response = client.post("/api/inquiries", json=payload)
    assert response.status_code == 422


def test_consulta_asociada_a_propiedad_publicada(client: TestClient) -> None:
    prop = make_property(code="ALM-FRM-01", title="Propiedad consultable")
    try:
        payload = dict(VALID_INQUIRY, property_code=prop.code)
        response = client.post("/api/inquiries", json=payload)
        assert response.status_code == 201

        inquiries = client.get(
            "/api/admin/inquiries", params={"q": "interesado@ejemplo.com"}
        )
        # Requiere token: lo pedimos con el de admin en el test de seguridad;
        # acá sólo validamos que el público no lo expone.
        assert inquiries.status_code == 401
    finally:
        delete_property_record("ALM-FRM-01")


def test_consulta_sobre_borrador_rechazada(client: TestClient) -> None:
    prop = make_property(
        code="ALM-FRM-02",
        title="Propiedad que sigue en borrador",
        publication_status="draft",
    )
    try:
        payload = dict(VALID_INQUIRY, property_code=prop.code)
        response = client.post("/api/inquiries", json=payload)
        assert response.status_code == 422
        assert response.json()["message"]
    finally:
        delete_property_record("ALM-FRM-02")


def test_consulta_sobre_codigo_inexistente_rechazada(client: TestClient) -> None:
    payload = dict(VALID_INQUIRY, property_code="ALM-XXXX-99")
    response = client.post("/api/inquiries", json=payload)
    assert response.status_code == 422


def test_limite_de_consultas(client: TestClient) -> None:
    """El séptimo envío supera el límite de la ventana y responde 429."""
    statuses = [
        client.post("/api/inquiries", json=dict(VALID_INQUIRY, email=f"q{index}@ejemplo.com"))
        .status_code
        for index in range(9)
    ]
    assert 429 in statuses
    assert statuses[-1] == 429


# ---------------------------------------------------------------------------
# Tasaciones
# ---------------------------------------------------------------------------
def test_solicitud_de_tasacion_valida(client: TestClient) -> None:
    response = client.post("/api/valuation-requests", json=VALID_VALUATION)
    assert response.status_code == 201, response.text
    assert response.json()["ok"] is True


def test_tasacion_campos_obligatorios(client: TestClient) -> None:
    response = client.post("/api/valuation-requests", json={"name": "X"})
    assert response.status_code == 422
    errors = response.json()["errors"]
    locations = {".".join(error["loc"]) for error in errors}
    assert any("email" in loc for loc in locations)
    assert any("locality" in loc for loc in locations)


def test_limite_de_tasaciones(client: TestClient) -> None:
    statuses = [
        client.post(
            "/api/valuation-requests", json=dict(VALID_VALUATION, email=f"t{index}@ejemplo.com")
        ).status_code
        for index in range(7)
    ]
    assert statuses[-1] == 429


# ---------------------------------------------------------------------------
# Solicitudes de publicación
# ---------------------------------------------------------------------------
def test_solicitud_de_publicacion_valida(client: TestClient) -> None:
    response = client.post("/api/listing-requests", json=VALID_LISTING)
    assert response.status_code == 201, response.text
    assert response.json()["id"]


def test_solicitud_de_publicacion_incompleta(client: TestClient) -> None:
    response = client.post("/api/listing-requests", json={"name": "Solo nombre"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Persistencia en panel
# ---------------------------------------------------------------------------
def test_los_formularios_quedan_registrados_en_el_panel(
    client: TestClient, admin_headers
) -> None:
    client.post("/api/inquiries", json=dict(VALID_INQUIRY, email="panel@ejemplo.com"))
    client.post("/api/valuation-requests", json=dict(VALID_VALUATION, email="panel2@ejemplo.com"))
    client.post("/api/listing-requests", json=dict(VALID_LISTING, email="panel3@ejemplo.com"))

    inquiries = client.get(
        "/api/admin/inquiries", params={"q": "panel@ejemplo.com"}, headers=admin_headers
    ).json()
    assert inquiries["total"] >= 1
    assert any(item["email"] == "panel@ejemplo.com" for item in inquiries["items"])

    valuations = client.get(
        "/api/admin/valuation-requests",
        params={"q": "panel2@ejemplo.com"},
        headers=admin_headers,
    ).json()
    assert any(item["email"] == "panel2@ejemplo.com" for item in valuations["items"])

    listings = client.get(
        "/api/admin/listing-requests",
        params={"q": "panel3@ejemplo.com"},
        headers=admin_headers,
    ).json()
    assert any(item["email"] == "panel3@ejemplo.com" for item in listings["items"])


def test_cambio_de_estado_y_nota_interna(
    client: TestClient, admin_headers, sample_inquiry
) -> None:
    updated = client.patch(
        f"/api/admin/inquiries/{sample_inquiry.id}",
        json={"status": "answered"},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "answered"

    note = client.post(
        f"/api/admin/inquiries/{sample_inquiry.id}/notes",
        json={"body": "Se llamó al interesado y quedó para el sábado."},
        headers=admin_headers,
    )
    assert note.status_code == 201
    assert note.json()["body"].startswith("Se llamó")

    # La nota queda sólo en el panel: la API pública no la expone.
    assert client.get("/api/inquiries").status_code in (404, 405, 401)


def test_estado_invalido_rechazado(client: TestClient, admin_headers, sample_inquiry) -> None:
    response = client.patch(
        f"/api/admin/inquiries/{sample_inquiry.id}",
        json={"status": "inventado"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_listado_de_consultas_requiere_token(client: TestClient) -> None:
    assert client.get("/api/admin/inquiries").status_code == 401
