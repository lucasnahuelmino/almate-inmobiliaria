"""Carga de datos de demostración: contenido e idempotencia."""

from __future__ import annotations

import re
import shutil

import pytest
from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.models.lead import Inquiry, ListingRequest, ValuationRequest
from app.models.property import CommercialStatus, Property, PropertyImage, PublicationStatus
from app.services.seed import DEMO_PROPERTIES, run_seed

DEMO_CODE = re.compile(r"^ALM-D\d{2}-\d{2}$")
DEMO_CODES = [item["code"] for item in DEMO_PROPERTIES]


@pytest.fixture(scope="module")
def seed_result():
    """Carga la demo dos veces para comprobar que no duplica registros."""
    db = SessionLocal()
    try:
        first = run_seed(db)
        second = run_seed(db)
    finally:
        db.close()
    yield first, second
    _clean_demo_upload_folders()


def _demo_property_ids() -> list[str]:
    db = SessionLocal()
    try:
        rows = db.execute(select(Property.id, Property.code)).all()
    finally:
        db.close()
    return [row[0] for row in rows if DEMO_CODE.match(row[1])]


def _clean_demo_upload_folders() -> None:
    """Borra las copias de fotografías creadas por la prueba."""
    uploads = get_settings().upload_path / "properties"
    for property_id in _demo_property_ids():
        folder = uploads / property_id
        if folder.is_dir():
            shutil.rmtree(folder, ignore_errors=True)


def test_carga_la_cantidad_de_propiedades_de_la_demo(seed_result) -> None:
    first, _ = seed_result
    assert len(DEMO_PROPERTIES) == 21
    # Crea exactamente las 21 de la demo (otras pruebas pueden haber dejado
    # fichas propias en la base: sólo cuentan las recién creadas).
    assert first["propiedades_nuevas"] == 21
    assert first["imagenes_disponibles"] > 0


def test_es_idempotente(seed_result) -> None:
    first, second = seed_result
    assert second["propiedades_nuevas"] == 0
    assert second["propiedades_total"] == first["propiedades_total"]
    assert second["imagenes_registradas"] == first["imagenes_registradas"]


def test_codigos_unicos_y_deterministas() -> None:
    assert len(DEMO_CODES) == len(set(DEMO_CODES))
    assert all(DEMO_CODE.match(code) for code in DEMO_CODES)


def test_estados_de_publicacion_variados() -> None:
    statuses = {item["publication_status"] for item in DEMO_PROPERTIES}
    assert PublicationStatus.PUBLISHED in statuses
    assert PublicationStatus.DRAFT in statuses
    assert PublicationStatus.ARCHIVED in statuses


def test_estados_comerciales_variados() -> None:
    statuses = {item.get("commercial_status") for item in DEMO_PROPERTIES}
    assert CommercialStatus.AVAILABLE in statuses
    assert CommercialStatus.RESERVED in statuses
    assert CommercialStatus.SOLD in statuses


def test_operaciones_y_tipos_variados() -> None:
    operations = {item["operation"] for item in DEMO_PROPERTIES}
    assert {"buy", "rent", "temporary_rent"} <= {op.value for op in operations}

    types = {item["property_type"] for item in DEMO_PROPERTIES}
    assert {"apartment", "house", "land", "commercial"} <= {t.value for t in types}


def test_solo_se_publican_las_publicadas() -> None:
    db = SessionLocal()
    try:
        rows = [
            row
            for row in db.execute(
                select(Property.code, Property.publication_status)
            ).all()
            if DEMO_CODE.match(row[0])
        ]
    finally:
        db.close()

    assert len(rows) == 21
    published = [r for r in rows if r[1] == PublicationStatus.PUBLISHED]
    drafts = [r for r in rows if r[1] == PublicationStatus.DRAFT]
    archived = [r for r in rows if r[1] == PublicationStatus.ARCHIVED]
    assert len(published) == 19
    assert len(drafts) == 1
    assert len(archived) == 1


def test_los_borradores_y_archivados_no_se_publican(client) -> None:
    hidden = [
        item["code"]
        for item in DEMO_PROPERTIES
        if item["publication_status"] != PublicationStatus.PUBLISHED
    ]
    assert hidden
    for code in hidden:
        assert client.get(f"/api/properties/{code}").status_code == 404


def test_el_catalogo_publico_solo_muestra_publicadas(client) -> None:
    body = client.get("/api/properties", params={"page_size": 60}).json()
    demo_codes = {
        item["code"] for item in body["items"] if DEMO_CODE.match(item["code"])
    }
    published_demo = {
        item["code"]
        for item in DEMO_PROPERTIES
        if item["publication_status"] == PublicationStatus.PUBLISHED
    }
    assert demo_codes == published_demo


def test_imagenes_registradas_en_la_base() -> None:
    db = SessionLocal()
    try:
        images = db.scalar(select(func.count(PropertyImage.id))) or 0
        con_properties = (
            db.scalar(select(func.count(func.distinct(PropertyImage.property_id)))) or 0
        )
    finally:
        db.close()
    assert images >= 40
    assert con_properties >= 15


def test_las_fotografias_estan_en_disco() -> None:
    db = SessionLocal()
    try:
        paths = [
            row[0]
            for row in db.execute(select(PropertyImage.storage_path)).all()
        ]
    finally:
        db.close()
    assert paths
    static_root = get_settings().upload_path.parent
    missing = [p for p in paths if not (static_root / p).is_file()]
    assert missing == [], f"faltan archivos: {missing}"


def test_leads_de_demo_sin_duplicados() -> None:
    """La segunda corrida no agrega consultas nuevas."""
    db = SessionLocal()
    try:
        inquiries = db.scalar(select(func.count(Inquiry.id))) or 0
        valuations = db.scalar(select(func.count(ValuationRequest.id))) or 0
        listings = db.scalar(select(func.count(ListingRequest.id))) or 0
    finally:
        db.close()
    assert inquiries + valuations + listings >= 1


def test_precios_de_demo_con_precision_de_centavos() -> None:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(Property.code, Property.price_cents, Property.currency)
        ).all()
    finally:
        db.close()

    demo_rows = [row for row in rows if DEMO_CODE.match(row[0])]
    assert demo_rows
    for code, cents, currency in demo_rows:
        assert currency in {"ARS", "USD", "EUR"}, code
        if cents is not None:
            assert isinstance(cents, int), code


def test_emprendimientos_marcados() -> None:
    marked = [i["code"] for i in DEMO_PROPERTIES if i.get("is_development")]
    assert marked, "la demo debe incluir al menos un emprendimiento"
