"""Catálogo público: filtros combinables, orden, paginación y detalle."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from conftest import delete_property_record, make_property

LOCALITY = "Tandil Pruebas"
OTHER_LOCALITY = "Bahía Blanca Pruebas"


@pytest.fixture(scope="module")
def catalog():
    """Propiedades de prueba con distintas operaciones y estados."""
    props = [
        make_property(
            code="ALM-CAT-01",
            title="Departamento compacto de pruebas",
            locality=LOCALITY,
            operation="buy",
            price="50000.00",
            bedrooms=2,
            bathrooms=1,
            garages=1,
            surface="60.00",
            apto_professional=True,
        ),
        make_property(
            code="ALM-CAT-02",
            title="Casa amplia de pruebas",
            locality=LOCALITY,
            operation="buy",
            property_type="house",
            price="150000.00",
            bedrooms=4,
            bathrooms=2,
            garages=2,
            surface="200.00",
        ),
        make_property(
            code="ALM-CAT-03",
            title="Departamento en alquiler de pruebas",
            locality=OTHER_LOCALITY,
            operation="rent",
            price="300000.00",
            currency="ARS",
            bedrooms=1,
            bathrooms=1,
            surface="40.00",
        ),
        make_property(
            code="ALM-CAT-04",
            title="Borrador que jamás se publica",
            locality=LOCALITY,
            operation="buy",
            price="10000.00",
            publication_status="draft",
        ),
        make_property(
            code="ALM-CAT-05",
            title="Emprendimiento de pruebas",
            locality=LOCALITY,
            operation="buy",
            price="80000.00",
            is_development=True,
            is_featured=True,
        ),
    ]
    yield {prop.code: prop for prop in props}
    for prop in props:
        delete_property_record(prop.code)


def codes(client: TestClient, **params) -> list[str]:
    response = client.get("/api/properties", params=params)
    assert response.status_code == 200, response.text
    return [item["code"] for item in response.json()["items"]]


# ---------------------------------------------------------------------------
# Visibilidad
# ---------------------------------------------------------------------------
def test_los_borradores_no_se_publican(client: TestClient, catalog) -> None:
    response = client.get("/api/properties", params={"locality": LOCALITY})
    body = response.json()
    assert "ALM-CAT-04" not in [item["code"] for item in body["items"]]
    assert all(
        item["publication_status"] == "published" for item in body["items"]
    )


def test_detalle_de_borrador_devuelve_404(client: TestClient, catalog) -> None:
    response = client.get("/api/properties/ALM-CAT-04")
    assert response.status_code == 404
    assert response.json()["message"]


def test_detalle_de_publicada(client: TestClient, catalog) -> None:
    response = client.get("/api/properties/ALM-CAT-01")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "ALM-CAT-01"
    assert body["price"] == "50000.00"
    assert body["currency"] == "USD"
    assert body["price_unit"] == "total"
    assert body["description"]
    assert isinstance(body["images"], list)


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
def test_filtro_por_operacion(client: TestClient, catalog) -> None:
    assert set(codes(client, operation="rent")) == {"ALM-CAT-03"}
    assert "ALM-CAT-03" not in codes(client, operation="buy")


def test_filtro_por_tipo(client: TestClient, catalog) -> None:
    assert set(codes(client, type="house")) == {"ALM-CAT-02"}


def test_filtro_por_localidad(client: TestClient, catalog) -> None:
    assert set(codes(client, locality=LOCALITY)) == {
        "ALM-CAT-01",
        "ALM-CAT-02",
        "ALM-CAT-05",
    }


def test_filtro_por_rango_de_precio(client: TestClient, catalog) -> None:
    assert set(codes(client, operation="buy", min_price=100000)) == {"ALM-CAT-02"}
    assert set(codes(client, operation="buy", max_price=60000)) == {"ALM-CAT-01"}


def test_filtro_por_dormitoros(client: TestClient, catalog) -> None:
    assert "ALM-CAT-02" in codes(client, operation="buy", bedrooms=3)
    assert "ALM-CAT-01" not in codes(client, operation="buy", bedrooms=3)


def test_filtro_por_banos(client: TestClient, catalog) -> None:
    assert set(codes(client, operation="buy", bathrooms=2)) == {"ALM-CAT-02"}


def test_filtro_por_superficie(client: TestClient, catalog) -> None:
    assert set(codes(client, operation="buy", min_surface=150)) == {"ALM-CAT-02"}
    assert "ALM-CAT-02" not in codes(client, operation="buy", max_surface=100)


def test_filtro_por_cochera(client: TestClient, catalog) -> None:
    assert "ALM-CAT-01" in codes(client, operation="buy", garage=True)


def test_filtro_apto_profesional(client: TestClient, catalog) -> None:
    assert "ALM-CAT-01" in codes(client, apto_professional=True)
    assert "ALM-CAT-02" not in codes(client, apto_professional=True)


def test_filtro_por_emprendimiento(client: TestClient, catalog) -> None:
    assert set(codes(client, development=True)) == {"ALM-CAT-05"}


def test_filtro_por_destacadas(client: TestClient, catalog) -> None:
    assert set(codes(client, featured=True)) == {"ALM-CAT-05"}


def test_busqueda_por_texto_y_codigo(client: TestClient, catalog) -> None:
    assert "ALM-CAT-02" in codes(client, q="Casa amplia")
    assert codes(client, q="ALM-CAT-02") == ["ALM-CAT-02"]


def test_filtros_combinados(client: TestClient, catalog) -> None:
    result = codes(client, operation="buy", type="apartment", locality=LOCALITY)
    assert set(result) == {"ALM-CAT-01", "ALM-CAT-05"}


def test_filtros_incompatibles_no_devuelven_nada(client: TestClient, catalog) -> None:
    assert codes(client, operation="rent", type="house") == []


def test_filtros_invalidos_devuelven_422(client: TestClient) -> None:
    response = client.get(
        "/api/properties", params={"min_price": 900000, "max_price": 100}
    )
    assert response.status_code == 422
    assert "message" in response.json()


def test_parametro_de_orden_invalido_devuelve_422(client: TestClient) -> None:
    response = client.get("/api/properties", params={"sort": "lo-que-sea"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Orden y paginación
# ---------------------------------------------------------------------------
def test_orden_por_precio_ascendente(client: TestClient, catalog) -> None:
    prices = [
        item["price"]
        for item in client.get(
            "/api/properties",
            params={"operation": "buy", "sort": "price_asc", "page_size": 50},
        ).json()["items"]
        if item["price"] is not None
    ]
    assert prices == sorted(prices, key=float)


def test_orden_por_precio_descendente(client: TestClient, catalog) -> None:
    prices = [
        item["price"]
        for item in client.get(
            "/api/properties",
            params={"operation": "buy", "sort": "price_desc", "page_size": 50},
        ).json()["items"]
        if item["price"] is not None
    ]
    assert prices == sorted(prices, key=float, reverse=True)


def test_paginacion_coherente(client: TestClient, catalog) -> None:
    first = client.get(
        "/api/properties", params={"operation": "buy", "page": 1, "page_size": 2}
    ).json()
    second = client.get(
        "/api/properties", params={"operation": "buy", "page": 2, "page_size": 2}
    ).json()

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1  # 3 publicadas en compra (la 4ª es borrador)
    assert first["total"] == second["total"] == 3
    assert first["pages"] == 2
    assert first["page"] == 1 and second["page"] == 2

    codes_page1 = {item["code"] for item in first["items"]}
    codes_page2 = {item["code"] for item in second["items"]}
    assert codes_page1.isdisjoint(codes_page2)


def test_pagina_fuera_de_rango_no_produce_error(client: TestClient, catalog) -> None:
    body = client.get(
        "/api/properties", params={"operation": "buy", "page": 99, "page_size": 2}
    ).json()
    assert body["items"] == []
    assert body["total"] == 3


def test_destacadas(client: TestClient, catalog) -> None:
    body = client.get("/api/properties/featured").json()
    assert "ALM-CAT-05" in [item["code"] for item in body]


def test_propiedades_similares(client: TestClient, catalog) -> None:
    response = client.get("/api/properties/ALM-CAT-01/similar")
    assert response.status_code == 200
    body = response.json()
    assert all(item["code"] != "ALM-CAT-01" for item in body)
    assert all(item["publication_status"] == "published" for item in body)


def test_localidades_publicadas_en_meta(client: TestClient, catalog) -> None:
    localities = client.get("/api/meta").json()["localities"]
    assert LOCALITY in localities
    assert "Tandil Pruebas" in localities
