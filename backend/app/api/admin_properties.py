"""CRUD administrativo de propiedades."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_staff
from app.database import get_db
from app.models.property import DEFAULT_UNIT_BY_OPERATION, Property, PublicationStatus
from app.models.user import User
from app.schemas.property import (
    PropertyAdminOut,
    PropertyCreate,
    PropertyUpdate,
    StatusUpdate,
)
from app.services import properties as service
from app.services.images import delete_property_files
from app.services.money import to_cents

router = APIRouter(prefix="/admin", tags=["Admin · Propiedades"])

AdminSort = Literal["recent", "created", "price_asc", "price_desc", "title"]


class AdminPropertyPage(BaseModel):
    items: list[PropertyAdminOut]
    total: int
    page: int
    page_size: int
    pages: int


ADMIN_SORTERS = {
    "recent": (Property.updated_at.desc(), Property.created_at.desc()),
    "created": (Property.created_at.desc(),),
    "price_asc": (Property.price_cents.is_(None), Property.price_cents.asc()),
    "price_desc": (Property.price_cents.is_(None), Property.price_cents.desc()),
    "title": (Property.title.asc(),),
}


def get_property_or_404(db: Session, identifier: str) -> Property:
    """Busca por UUID interno o por código de referencia."""
    prop = db.scalar(
        service.base_property_query().where(
            or_(Property.id == identifier, Property.code == identifier.upper().strip())
        )
    )
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No se encontró la propiedad indicada."},
        )
    return prop


def _apply_published_at(prop: Property) -> None:
    """Registra la fecha de publicación la primera vez que se publica."""
    if prop.publication_status == PublicationStatus.PUBLISHED and prop.published_at is None:
        from app.models.common import utcnow

        prop.published_at = utcnow()


@router.get(
    "/properties",
    response_model=AdminPropertyPage,
    summary="Listado administrativo con búsqueda y filtros",
)
def list_admin_properties(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
    q: str | None = Query(None, max_length=80, description="Código, título o localidad"),
    operation: str | None = Query(None),
    type: str | None = Query(None),
    publication_status: PublicationStatus | None = Query(None),
    commercial_status: str | None = Query(None),
    locality: str | None = Query(None, max_length=120),
    sort: AdminSort = Query("recent"),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
) -> AdminPropertyPage:
    query = service.base_property_query()

    if q:
        term = f"%{q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Property.title).like(term),
                func.lower(Property.code).like(term),
                func.lower(Property.locality).like(term),
                func.lower(Property.neighborhood).like(term),
            )
        )
    if operation:
        query = query.where(Property.operation == operation)
    if type:
        query = query.where(Property.property_type == type)
    if publication_status:
        query = query.where(Property.publication_status == publication_status)
    if commercial_status:
        query = query.where(Property.commercial_status == commercial_status)
    if locality:
        query = query.where(func.lower(Property.locality) == locality.lower())

    query = query.order_by(*ADMIN_SORTERS.get(sort, ADMIN_SORTERS["recent"]))
    items, total = service.paginate(query, db, page, page_size)
    return AdminPropertyPage(
        items=[service.to_admin(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=service.page_count(total, page_size),
    )


@router.post(
    "/properties",
    response_model=PropertyAdminOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear propiedad",
)
def create_property(
    payload: PropertyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
) -> PropertyAdminOut:
    prop = Property(
        **payload.model_dump(exclude={"price", "expenses", "price_unit"}),
        price_cents=to_cents(payload.price),
        expenses_cents=to_cents(payload.expenses),
        price_unit=payload.price_unit or DEFAULT_UNIT_BY_OPERATION[payload.operation],
        code=service.generate_code(db),
        created_by=user.id,
    )
    _apply_published_at(prop)
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return service.to_admin(prop)


@router.get(
    "/properties/{identifier}",
    response_model=PropertyAdminOut,
    summary="Detalle administrativo de una propiedad",
)
def admin_property_detail(
    identifier: str, db: Session = Depends(get_db), _: User = Depends(require_staff)
) -> PropertyAdminOut:
    return service.to_admin(get_property_or_404(db, identifier))


@router.patch(
    "/properties/{identifier}",
    response_model=PropertyAdminOut,
    summary="Editar propiedad (parcial)",
)
def update_property(
    identifier: str,
    payload: PropertyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
) -> PropertyAdminOut:
    prop = get_property_or_404(db, identifier)
    data = payload.model_dump(exclude_unset=True)

    price = data.pop("price", None)
    expenses = data.pop("expenses", None)
    if "price" in payload.model_fields_set:
        prop.price_cents = to_cents(price)
    if "expenses" in payload.model_fields_set:
        prop.expenses_cents = to_cents(expenses)

    for field, value in data.items():
        setattr(prop, field, value)

    # Si cambió la operación y no se indicó la unidad, se rederiva.
    if "price_unit" not in payload.model_fields_set and "operation" in payload.model_fields_set:
        prop.price_unit = DEFAULT_UNIT_BY_OPERATION[prop.operation]

    _apply_published_at(prop)
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return service.to_admin(prop)


@router.post(
    "/properties/{identifier}/status",
    response_model=PropertyAdminOut,
    summary="Cambiar estado comercial y/o de publicación",
)
def change_status(
    identifier: str,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> PropertyAdminOut:
    if payload.publication_status is None and payload.commercial_status is None:
        raise HTTPException(
            status_code=422,
            detail={"message": "Indicá qué estado querés cambiar."},
        )
    prop = get_property_or_404(db, identifier)
    if payload.publication_status is not None:
        prop.publication_status = payload.publication_status
    if payload.commercial_status is not None:
        prop.commercial_status = payload.commercial_status
    _apply_published_at(prop)
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return service.to_admin(prop)


@router.delete(
    "/properties/{identifier}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar propiedad y sus fotografías (sólo rol admin)",
)
def delete_property(
    identifier: str, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    prop = get_property_or_404(db, identifier)
    delete_property_files(prop)
    db.delete(prop)
    db.commit()
