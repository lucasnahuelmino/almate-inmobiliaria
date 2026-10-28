"""Lógica de consulta y serialización de propiedades."""

from __future__ import annotations

import random
import string
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.property import (
    Operation,
    Property,
    PropertyImage,
    PublicationStatus,
)
from app.models.lead import Inquiry
from app.schemas.property import (
    PropertyAdminOut,
    PropertyDetailOut,
    PropertyImageAdminOut,
    PropertyImageOut,
    PropertySummaryOut,
    PublicFilters,
)
from app.services.money import from_cents, to_cents

# ---------------------------------------------------------------------------
# Serialización
# ---------------------------------------------------------------------------

def image_out(image: PropertyImage) -> PropertyImageOut:
    return PropertyImageOut(
        id=image.id,
        url=image.url,
        alt=image.alt_text or "",
        is_main=image.is_main,
        sort_order=image.sort_order,
    )


def image_admin_out(image: PropertyImage) -> PropertyImageAdminOut:
    return PropertyImageAdminOut(
        id=image.id,
        url=image.url,
        alt=image.alt_text or "",
        is_main=image.is_main,
        sort_order=image.sort_order,
        filename=image.filename,
        mime_type=image.mime_type,
        size_bytes=image.size_bytes,
        created_at=image.created_at,
    )


def _ordered_images(prop: Property) -> list[PropertyImage]:
    images = list(prop.images or [])
    images.sort(key=lambda img: (not img.is_main, img.sort_order, img.id))
    return images


def _base_fields(prop: Property) -> dict:
    return {
        "code": prop.code,
        "title": prop.title,
        "operation": prop.operation,
        "property_type": prop.property_type,
        "is_development": prop.is_development,
        "is_featured": prop.is_featured,
        "price": from_cents(prop.price_cents),
        "currency": prop.currency,
        "price_unit": prop.price_unit,
        "expenses": from_cents(prop.expenses_cents),
        "commercial_status": prop.commercial_status,
        "publication_status": prop.publication_status,
        "country": prop.country,
        "province": prop.province,
        "department": prop.department,
        "locality": prop.locality,
        "neighborhood": prop.neighborhood,
        # La dirección sólo se publica si el propietario autorizó.
        "address": prop.address if prop.address_is_public else None,
        "address_is_public": prop.address_is_public,
        "rooms": prop.rooms,
        "bedrooms": prop.bedrooms,
        "bathrooms": prop.bathrooms,
        "garages": prop.garages,
        "surface_covered": prop.surface_covered,
        "surface_total": prop.surface_total,
        "apto_professional": prop.apto_professional,
        "published_at": prop.published_at,
    }


def to_summary(prop: Property) -> PropertySummaryOut:
    images = _ordered_images(prop)
    return PropertySummaryOut(
        **_base_fields(prop),
        image=image_out(images[0]) if images else None,
    )


def to_detail(prop: Property) -> PropertyDetailOut:
    images = _ordered_images(prop)
    return PropertyDetailOut(
        **_base_fields(prop),
        description=prop.description or "",
        toilets=prop.toilets,
        antiquity_years=prop.antiquity_years,
        surface_semicovered=prop.surface_semicovered,
        services=list(prop.services or []),
        images=[image_out(img) for img in images],
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


def to_admin(prop: Property) -> PropertyAdminOut:
    data = to_detail(prop).model_dump()  # incluye created_at / updated_at
    images = _ordered_images(prop)
    # `images` se reconstruye con metadatos extra del panel: se descarta el de to_detail.
    data.pop("images", None)
    return PropertyAdminOut(
        **data,
        id=prop.id,
        created_by=prop.created_by,
        images=[image_admin_out(img) for img in images],
    )


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------
def base_property_query(*, include_archived: bool = False) -> Select:
    return select(Property).options(selectinload(Property.images))


def public_query() -> Select:
    """Sólo propiedades publicadas (nunca borradores ni archivadas)."""
    return base_property_query().where(
        Property.publication_status == PublicationStatus.PUBLISHED
    )


def apply_filters(query: Select, filters: PublicFilters) -> Select:
    """Aplica filtros combinables sobre el catálogo público."""
    if filters.operation:
        query = query.where(Property.operation == filters.operation)
    if filters.type:
        query = query.where(Property.property_type == filters.type)
    if filters.development is not None:
        query = query.where(Property.is_development.is_(filters.development))
    if filters.featured is not None:
        query = query.where(Property.is_featured.is_(filters.featured))
    if filters.locality:
        query = query.where(func.lower(Property.locality) == filters.locality.lower())
    if filters.province:
        query = query.where(func.lower(Property.province) == filters.province.lower())
    if filters.q:
        term = f"%{filters.q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Property.title).like(term),
                func.lower(Property.description).like(term),
                func.lower(Property.locality).like(term),
                func.lower(Property.neighborhood).like(term),
                func.lower(Property.code).like(term),
            )
        )

    min_cents = to_cents(filters.min_price)
    max_cents = to_cents(filters.max_price)
    if min_cents is not None:
        query = query.where(Property.price_cents.is_not(None), Property.price_cents >= min_cents)
    if max_cents is not None:
        query = query.where(Property.price_cents.is_not(None), Property.price_cents <= max_cents)

    if filters.bedrooms is not None:
        query = query.where(Property.bedrooms.is_not(None), Property.bedrooms >= filters.bedrooms)
    if filters.bathrooms is not None:
        query = query.where(Property.bathrooms.is_not(None), Property.bathrooms >= filters.bathrooms)

    surface_col = Property.surface_total
    if filters.min_surface is not None:
        query = query.where(surface_col.is_not(None), surface_col >= filters.min_surface)
    if filters.max_surface is not None:
        query = query.where(surface_col.is_not(None), surface_col <= filters.max_surface)

    if filters.garage:
        query = query.where(Property.garages.is_not(None), Property.garages >= 1)
    if filters.apto_professional:
        query = query.where(Property.apto_professional.is_(True))
    return query


SORTERS = {
    "recent": (Property.published_at.desc(), Property.created_at.desc()),
    "oldest": (Property.published_at.asc(), Property.created_at.asc()),
    "price_asc": (Property.price_cents.is_(None), Property.price_cents.asc()),
    "price_desc": (Property.price_cents.is_(None), Property.price_cents.desc()),
}


def apply_sort(query: Select, sort: str) -> Select:
    return query.order_by(*SORTERS.get(sort, SORTERS["recent"]))


def paginate(query: Select, db: Session, page: int, page_size: int) -> tuple[list, int]:
    """Devuelve (items, total) para la página solicitada."""
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all())
    return items, int(total)


def page_count(total: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return max(1, (total + page_size - 1) // page_size)


# ---------------------------------------------------------------------------
# Código de referencia
# ---------------------------------------------------------------------------
def generate_code(db: Session) -> str:
    """Genera un código único tipo `ALM-4F7K-26` (legible y no enumerativo)."""
    from datetime import datetime

    year = datetime.now().strftime("%y")
    for _ in range(50):
        block = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        code = f"ALM-{block}-{year}"
        exists = db.scalar(select(Property.id).where(Property.code == code))
        if not exists:
            return code
    raise RuntimeError("No fue posible generar un código de referencia único.")


def localities(db: Session) -> list[str]:
    """Localidades publicadas (para el combo de filtros)."""
    rows = db.scalars(
        select(func.distinct(Property.locality))
        .where(
            Property.publication_status == PublicationStatus.PUBLISHED,
            Property.locality.is_not(None),
        )
        .order_by(Property.locality)
    ).all()
    return [row for row in rows if row]


def operations_in_use(db: Session) -> list[Operation]:
    rows = db.scalars(
        select(func.distinct(Property.operation))
        .where(Property.publication_status == PublicationStatus.PUBLISHED)
    ).all()
    return list(rows)


def lead_count(db: Session) -> int:
    """Total de consultas recibidas (métrica del dashboard)."""
    return int(db.scalar(select(func.count(Inquiry.id))) or 0)
