"""Configuración de las pruebas de backend.

Usa una base de datos SQLite temporal (`./test_almate.db`) que se elimina al
iniciar. La variable `DATABASE_URL` se define **antes** de importar `app` para
que la configuración quede congelada apuntando a esa base.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

TEST_DB = BACKEND_DIR / "test_almate.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "clave-de-prueba-suficientemente-larga-0123456789"

if TEST_DB.exists():
    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{TEST_DB}{suffix}")
        if path.exists():
            path.unlink()

from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, init_database  # noqa: E402
from app.main import app  # noqa: E402
from app.models.lead import (  # noqa: E402
    Inquiry,
    InquiryKind,
    ListingRequest,
    ValuationRequest,
)
from app.models.property import (  # noqa: E402
    CommercialStatus,
    Operation,
    Property,
    PropertyType,
    PublicationStatus,
)
from app.models.user import User, UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services.money import to_cents  # noqa: E402
from app.services.ratelimit import (  # noqa: E402
    form_limiter,
    inquiry_limiter,
    login_limiter,
)

ADMIN_EMAIL = "admin@test.com"
EDITOR_EMAIL = "editor@test.com"
PASSWORD = "ClaveSegura123!"


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    init_database()


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Cada prueba arranca con el contador de límites en cero.

    Los límites por IP se prueban explícitamente en `test_security.py`; sin
    este reinicio, las pruebas anteriores agotarían la cuota compartida.
    """
    for limiter in (login_limiter, inquiry_limiter, form_limiter):
        limiter._hits.clear()
    yield
    for limiter in (login_limiter, inquiry_limiter, form_limiter):
        limiter._hits.clear()


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _create_user(email: str, name: str, role: UserRole) -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one_or_none()
        if user is None:
            user = User(email=email, full_name=name)
            db.add(user)
        user.password_hash = hash_password(PASSWORD)
        user.role = role
        user.is_active = True
        db.commit()
    finally:
        db.close()

    with TestClient(app) as temp_client:
        response = temp_client.post(
            "/api/auth/login", json={"email": email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        return response.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(client: TestClient) -> dict[str, str]:
    """Cabeceras con token de un usuario con rol admin."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).one_or_none()
        if user is None:
            user = User(email=ADMIN_EMAIL, full_name="Admin de pruebas")
            db.add(user)
        user.password_hash = hash_password(PASSWORD)
        user.role = UserRole.ADMIN
        user.is_active = True
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def editor_headers(client: TestClient) -> dict[str, str]:
    """Cabeceras con token de un usuario con rol editor (sin permisos de admin)."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == EDITOR_EMAIL).one_or_none()
        if user is None:
            user = User(email=EDITOR_EMAIL, full_name="Editor de pruebas")
            db.add(user)
        user.password_hash = hash_password(PASSWORD)
        user.role = UserRole.EDITOR
        user.is_active = True
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/auth/login", json={"email": EDITOR_EMAIL, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def make_property(
    *,
    title: str = "Departamento de pruebas en Quilmes",
    operation: Operation = Operation.BUY,
    property_type: PropertyType = PropertyType.APARTMENT,
    publication_status: PublicationStatus = PublicationStatus.PUBLISHED,
    commercial_status: CommercialStatus = CommercialStatus.AVAILABLE,
    locality: str = "Quilmes",
    price: str = "75000.00",
    bedrooms: int = 2,
    bathrooms: int = 1,
    garages: int = 1,
    surface: str = "60.00",
    **extra,
) -> Property:
    """Crea y persiste una propiedad de prueba (helper compartido)."""
    db = SessionLocal()
    try:
        prop = Property(
            code=extra.pop("code", "ALM-TST-26"),
            title=title,
            description=extra.pop("description", "Descripción de prueba para el catálogo."),
            operation=operation,
            property_type=property_type,
            publication_status=publication_status,
            commercial_status=commercial_status,
            locality=locality,
            neighborhood=extra.pop("neighborhood", "Centro"),
            country="Argentina",
            province="Buenos Aires",
            price_cents=to_cents(price),
            currency=extra.pop("currency", "USD"),
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            garages=garages,
            surface_covered=surface,
            surface_total=surface,
            published_at=extra.pop("published_at", None),
            **extra,
        )
        from app.models.common import utcnow

        if publication_status == PublicationStatus.PUBLISHED and prop.published_at is None:
            prop.published_at = utcnow()
        db.add(prop)
        db.commit()
        db.refresh(prop)
        return prop
    finally:
        db.close()


def delete_property_record(code: str) -> None:
    db = SessionLocal()
    try:
        prop = db.query(Property).filter(Property.code == code).one_or_none()
        if prop is not None:
            db.delete(prop)
            db.commit()
    finally:
        db.close()


@pytest.fixture
def sample_property() -> Property:
    prop = make_property()
    yield prop
    delete_property_record(prop.code)


@pytest.fixture
def sample_inquiry(client: TestClient) -> Inquiry:
    response = client.post(
        "/api/inquiries",
        json={
            "name": "Consulta de prueba",
            "email": "consulta@test.com",
            "message": "Mensaje de prueba suficientemente largo.",
        },
    )
    assert response.status_code == 201, response.text
    # Devuelve la fila recién creada, ya con la sesión cerrada de forma segura.
    db = SessionLocal()
    try:
        inquiry = db.get(Inquiry, response.json()["id"])
        db.expunge(inquiry)
        return inquiry
    finally:
        db.close()
