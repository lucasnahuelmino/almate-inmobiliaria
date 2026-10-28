"""CRUD administrativo de propiedades: alta, edición, estados y baja."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from conftest import delete_property_record, make_property

NUEVA = {
    "title": "Departamento de carga administrativa",
    "description": "Ficha creada durante las pruebas del panel administrativo.",
    "operation": "buy",
    "property_type": "apartment",
    "price": "75000.55",
    "currency": "USD",
    "locality": "Quilmes",
    "neighborhood": "Centro",
    "bedrooms": 2,
    "bathrooms": 1,
    "surface_covered": "60.00",
    "surface_total": "66.00",
    "publication_status": "draft",
}


def test_requiere_autenticacion(client: TestClient) -> None:
    assert client.get("/api/admin/properties").status_code == 401
    assert client.post("/api/admin/properties", json=NUEVA).status_code == 401


def test_alta_de_propiedad(client: TestClient, admin_headers) -> None:
    response = client.post("/api/admin/properties", json=NUEVA, headers=admin_headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert re.match(r"^ALM-[A-Z0-9]{4}-\d{2}$", body["code"])
    assert body["price"] == "75000.55"
    assert body["price_unit"] == "total"
    assert body["publication_status"] == "draft"
    assert body["created_at"]

    # Un borrador no debe aparecer en el catálogo público.
    public = client.get(
        "/api/properties", params={"locality": "Quilmes", "page_size": 60}
    ).json()
    assert body["code"] not in [item["code"] for item in public["items"]]

    # Limpieza.
    assert (
        client.delete(f"/api/admin/properties/{body['code']}", headers=admin_headers).status_code
        == 204
    )


def test_alta_con_datos_invalidos(client: TestClient, admin_headers) -> None:
    payload = dict(NUEVA)
    payload["title"] = "abc"  # demasiado corto
    payload["price"] = "-5"
    response = client.post("/api/admin/properties", json=payload, headers=admin_headers)
    assert response.status_code == 422
    body = response.json()
    assert body["message"]
    assert isinstance(body["errors"], list)


def test_alta_sin_campos_obligatorios(client: TestClient, admin_headers) -> None:
    response = client.post("/api/admin/properties", json={}, headers=admin_headers)
    assert response.status_code == 422
    assert response.json()["errors"]


def test_edicion_parcial(client: TestClient, admin_headers) -> None:
    prop = make_property(code="ALM-ADM-01", title="Propiedad para editar")
    try:
        response = client.patch(
            f"/api/admin/properties/{prop.code}",
            json={"title": "Título actualizado desde el panel", "price": "81000.10"},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["title"] == "Título actualizado desde el panel"
        assert body["price"] == "81000.10"

        # El resto de los campos quedó intacto.
        assert body["locality"] == prop.locality
        assert body["publication_status"] == "published"
    finally:
        delete_property_record("ALM-ADM-01")


def test_edicion_no_pisa_campos_ausentes(client: TestClient, admin_headers) -> None:
    prop = make_property(code="ALM-ADM-02", title="Propiedad con descripción")
    original_description = prop.description
    try:
        client.patch(
            f"/api/admin/properties/{prop.code}",
            json={"bedrooms": 3},
            headers=admin_headers,
        )
        detail = client.get(
            f"/api/admin/properties/{prop.code}", headers=admin_headers
        ).json()
        assert detail["description"] == original_description
        assert detail["bedrooms"] == 3
    finally:
        delete_property_record("ALM-ADM-02")


def test_cambio_de_estado_de_publicacion(client: TestClient, admin_headers) -> None:
    prop = make_property(
        code="ALM-ADM-03",
        title="Propiedad para publicar",
        publication_status="draft",
    )
    try:
        # Sigue invisible para el público.
        assert client.get(f"/api/properties/{prop.code}").status_code == 404

        response = client.post(
            f"/api/admin/properties/{prop.code}/status",
            json={"publication_status": "published"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["publication_status"] == "published"
        assert response.json()["published_at"]

        # Ahora sí se ve en el catálogo.
        assert client.get(f"/api/properties/{prop.code}").status_code == 200

        # Cambio de estado comercial independiente.
        response = client.post(
            f"/api/admin/properties/{prop.code}/status",
            json={"commercial_status": "reserved"},
            headers=admin_headers,
        )
        assert response.json()["commercial_status"] == "reserved"
        assert response.json()["publication_status"] == "published"
    finally:
        delete_property_record("ALM-ADM-03")


def test_cambio_de_estado_vacio_es_invalido(client: TestClient, admin_headers) -> None:
    prop = make_property(code="ALM-ADM-04", title="Propiedad sin cambios")
    try:
        response = client.post(
            f"/api/admin/properties/{prop.code}/status", json={}, headers=admin_headers
        )
        assert response.status_code == 422
    finally:
        delete_property_record("ALM-ADM-04")


def test_listado_administrativo_incluye_borradores(
    client: TestClient, admin_headers
) -> None:
    make_property(
        code="ALM-ADM-05",
        title="Borrador administrativo",
        publication_status="draft",
        locality="San Martín Prueba",
    )
    try:
        response = client.get(
            "/api/admin/properties",
            params={"q": "BORRADOR ADMINISTRATIVO", "page_size": 50},
            headers=admin_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        assert any(item["code"] == "ALM-ADM-05" for item in body["items"])

        # Mismo texto en el catálogo público: nada.
        public = client.get(
            "/api/properties", params={"q": "BORRADOR ADMINISTRATIVO"}
        ).json()
        assert public["total"] == 0
    finally:
        delete_property_record("ALM-ADM-05")


def test_listado_administrativo_filtra_por_estado(
    client: TestClient, admin_headers
) -> None:
    make_property(
        code="ALM-ADM-06",
        title="Propiedad archivada de prueba",
        publication_status="archived",
        locality="Lomas Prueba",
    )
    try:
        body = client.get(
            "/api/admin/properties",
            params={"publication_status": "archived", "page_size": 100},
            headers=admin_headers,
        ).json()
        assert any(item["code"] == "ALM-ADM-06" for item in body["items"])
        assert all(item["publication_status"] == "archived" for item in body["items"])
    finally:
        delete_property_record("ALM-ADM-06")


def test_paginacion_del_listado_administrativo(
    client: TestClient, admin_headers
) -> None:
    body = client.get(
        "/api/admin/properties", params={"page": 1, "page_size": 3}, headers=admin_headers
    ).json()
    assert len(body["items"]) <= 3
    assert body["page"] == 1
    assert body["total"] >= len(body["items"])
    assert body["pages"] >= 1


def test_detalle_administrativo_por_id_y_por_codigo(
    client: TestClient, admin_headers
) -> None:
    prop = make_property(code="ALM-ADM-07", title="Propiedad con ambos identificadores")
    try:
        by_code = client.get(
            f"/api/admin/properties/{prop.code}", headers=admin_headers
        )
        by_id = client.get(f"/api/admin/properties/{prop.id}", headers=admin_headers)
        assert by_code.status_code == by_id.status_code == 200
        assert by_code.json()["id"] == by_id.json()["id"]
    finally:
        delete_property_record("ALM-ADM-07")


def test_eliminar_propiedad(client: TestClient, admin_headers) -> None:
    prop = make_property(code="ALM-ADM-08", title="Propiedad a eliminar")
    response = client.delete(
        f"/api/admin/properties/{prop.code}", headers=admin_headers
    )
    assert response.status_code == 204
    assert client.get(f"/api/admin/properties/{prop.code}", headers=admin_headers).status_code == 404
    assert client.get(f"/api/properties/{prop.code}").status_code == 404


def test_eliminar_inexistente_devuelve_404(client: TestClient, admin_headers) -> None:
    response = client.delete(
        "/api/admin/properties/ALM-XXXX-99", headers=admin_headers
    )
    assert response.status_code == 404


def test_editor_puede_crear_y_editar(client: TestClient, editor_headers) -> None:
    payload = dict(NUEVA)
    payload["title"] = "Propiedad creada por el editor"
    response = client.post("/api/admin/properties", json=payload, headers=editor_headers)
    assert response.status_code == 201
    code = response.json()["code"]
    try:
        patched = client.patch(
            f"/api/admin/properties/{code}",
            json={"title": "Propiedad renombrada por el editor"},
            headers=editor_headers,
        )
        assert patched.status_code == 200
        assert patched.json()["title"] == "Propiedad renombrada por el editor"
    finally:
        client.delete(f"/api/admin/properties/{code}", headers=editor_headers)


def test_unidad_de_precio_se_deriva_de_la_operacion(
    client: TestClient, admin_headers
) -> None:
    payload = dict(NUEVA)
    payload["title"] = "Departamento en alquiler mensual"
    payload["operation"] = "rent"
    payload["price"] = "350000"
    payload["currency"] = "ARS"
    response = client.post("/api/admin/properties", json=payload, headers=admin_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["price_unit"] == "monthly"
    assert body["price"] == "350000.00"
    client.delete(
        f"/api/admin/properties/{body['code']}", headers=admin_headers
    )


def test_alquiler_temporal_expresa_precio_por_dia(
    client: TestClient, admin_headers
) -> None:
    payload = dict(NUEVA)
    payload["title"] = "Casa temporal de prueba"
    payload["operation"] = "temporary_rent"
    payload["price"] = "65000"
    response = client.post("/api/admin/properties", json=payload, headers=admin_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["price_unit"] == "daily"
    client.delete(
        f"/api/admin/properties/{body['code']}", headers=admin_headers
    )
