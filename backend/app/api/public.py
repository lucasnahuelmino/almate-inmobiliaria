"""Endpoints públicos: catálogo, detalle, metadatos de filtros y configuración."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import validation_detail
from app.config import get_settings
from app.database import get_db
from app.models.property import (
    CommercialStatus,
    Operation,
    Property,
    PropertyType,
    PublicationStatus,
)
from app.models.settings import BusinessSettings
from app.schemas.property import (
    PropertyDetailOut,
    PropertyPage,
    PropertySummaryOut,
    PublicFilters,
    SortOption,
)
from app.schemas.settings import PublicSettingsOut
from app.services import properties as service

router = APIRouter(tags=["Público"])

OPERATION_LABELS = {
    Operation.BUY: "Comprar",
    Operation.RENT: "Alquilar",
    Operation.TEMPORARY_RENT: "Alquiler temporal",
}

PROPERTY_TYPE_LABELS = {
    PropertyType.APARTMENT: "Departamento",
    PropertyType.HOUSE: "Casa",
    PropertyType.PH: "PH",
    PropertyType.LAND: "Terreno",
    PropertyType.COMMERCIAL: "Local comercial",
    PropertyType.OFFICE: "Oficina",
    PropertyType.GARAGE: "Cochera",
}

STATUS_LABELS = {
    CommercialStatus.AVAILABLE: "Disponible",
    CommercialStatus.RESERVED: "Reservado",
    CommercialStatus.SOLD: "Vendido",
    CommercialStatus.RENTED: "Alquilado",
}


def parse_filters(
    operation: Operation | None = Query(None, description="buy | rent | temporary_rent"),
    type: PropertyType | None = Query(None, alias="type", description="Tipo de propiedad"),
    locality: str | None = Query(None, max_length=120),
    province: str | None = Query(None, max_length=120),
    q: str | None = Query(None, max_length=80, description="Texto libre"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    bedrooms: int | None = Query(None, ge=0, le=50),
    bathrooms: int | None = Query(None, ge=0, le=50),
    min_surface: float | None = Query(None, ge=0),
    max_surface: float | None = Query(None, ge=0),
    garage: bool | None = Query(None),
    apto_professional: bool | None = Query(None),
    development: bool | None = Query(None),
    featured: bool | None = Query(None),
    sort: SortOption = Query("recent"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=60),
) -> PublicFilters:
    """Construye y valida los filtros del catálogo a partir de la query string."""
    try:
        return PublicFilters(
            operation=operation,
            type=type,
            locality=locality,
            province=province,
            q=q,
            min_price=min_price,
            max_price=max_price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            min_surface=min_surface,
            max_surface=max_surface,
            garage=garage,
            apto_professional=apto_professional,
            development=development,
            featured=featured,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "Filtros inválidos.", "errors": validation_detail(exc)},
        ) from exc


@router.get("/health", summary="Comprobación de estado")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {"status": "ok", "app": get_settings().app_name}


@router.get("/meta", summary="Opciones disponibles para los filtros")
def meta(db: Session = Depends(get_db)) -> dict:
    """Devuelve operaciones, tipos, monedas, localidades y estados para la UI."""
    return {
        "operations": [
            {"value": op.value, "label": label} for op, label in OPERATION_LABELS.items()
        ],
        "property_types": [
            {"value": t.value, "label": label} for t, label in PROPERTY_TYPE_LABELS.items()
        ],
        "commercial_statuses": [
            {"value": s.value, "label": label} for s, label in STATUS_LABELS.items()
        ],
        "currencies": ["ARS", "USD", "EUR"],
        "localities": service.localities(db),
        "sort_options": [
            {"value": "recent", "label": "Más recientes"},
            {"value": "price_asc", "label": "Menor precio"},
            {"value": "price_desc", "label": "Mayor precio"},
            {"value": "oldest", "label": "Más antiguas"},
        ],
    }


@router.get(
    "/properties",
    response_model=PropertyPage,
    summary="Catálogo público con filtros combinables",
)
def list_properties(
    filters: PublicFilters = Depends(parse_filters),
    db: Session = Depends(get_db),
) -> PropertyPage:
    query = service.apply_sort(
        service.apply_filters(service.public_query(), filters), filters.sort
    )
    items, total = service.paginate(query, db, filters.page, filters.page_size)
    return PropertyPage(
        items=[service.to_summary(item) for item in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=service.page_count(total, filters.page_size),
    )


@router.get(
    "/properties/featured",
    response_model=list[PropertySummaryOut],
    summary="Propiedades destacadas",
)
def featured_properties(
    limit: int = Query(6, ge=1, le=12), db: Session = Depends(get_db)
) -> list[PropertySummaryOut]:
    query = (
        service.public_query()
        .where(Property.is_featured.is_(True))
        .order_by(Property.published_at.desc().nullslast(), Property.created_at.desc())
        .limit(limit)
    )
    items = list(db.scalars(query).all())
    return [service.to_summary(item) for item in items]


def _published_property(db: Session, code: str) -> Property:
    """Devuelve la propiedad publicada o lanza 404 (sin filtrar borradores)."""
    prop = db.scalar(service.public_query().where(Property.code == code.upper().strip()))
    if prop is None:
        raise HTTPException(status_code=404, detail={"message": "Propiedad no encontrada."})
    return prop


@router.get(
    "/properties/{code}",
    response_model=PropertyDetailOut,
    summary="Detalle de una propiedad publicada",
)
def property_detail(code: str, db: Session = Depends(get_db)) -> PropertyDetailOut:
    return service.to_detail(_published_property(db, code))


@router.get(
    "/properties/{code}/similar",
    response_model=list[PropertySummaryOut],
    summary="Propiedades similares",
)
def similar_properties(
    code: str, limit: int = Query(4, ge=1, le=8), db: Session = Depends(get_db)
) -> list[PropertySummaryOut]:
    current = _published_property(db, code)
    query = (
        service.public_query()
        .where(
            Property.id != current.id,
            Property.publication_status == PublicationStatus.PUBLISHED,
        )
        .order_by(Property.published_at.desc().nullslast())
        .limit(40)
    )
    candidates = list(db.scalars(query).all())

    def score(other: Property) -> int:
        value = 0
        if other.property_type == current.property_type:
            value += 3
        if other.operation == current.operation:
            value += 2
        if (other.locality or "").lower() == (current.locality or "").lower():
            value += 2
        if other.is_featured:
            value += 1
        return value

    candidates.sort(key=score, reverse=True)
    selected = [item for item in candidates if score(item) > 0][:limit]
    if len(selected) < limit:
        selected += [item for item in candidates if item not in selected]
        selected = selected[:limit]
    return [service.to_summary(item) for item in selected]


@router.get(
    "/settings",
    response_model=PublicSettingsOut,
    summary="Configuración pública del negocio",
)
def public_settings(db: Session = Depends(get_db)) -> PublicSettingsOut:
    return PublicSettingsOut.model_validate(BusinessSettings.get_or_create(db))
