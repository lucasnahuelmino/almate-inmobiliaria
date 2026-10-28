"""Administración de consultas, tasaciones y solicitudes de publicación."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_staff
from app.database import get_db
from app.models.lead import (
    Inquiry,
    InternalNote,
    LeadStatus,
    ListingRequest,
    ValuationRequest,
)
from app.models.user import User
from app.schemas.lead import (
    InquiryOut,
    LeadStatusUpdate,
    ListingRequestOut,
    NoteCreate,
    NoteOut,
    ValuationRequestOut,
)

router = APIRouter(prefix="/admin", tags=["Admin · Consultas"])


class LeadPage(BaseModel):
    items: list[InquiryOut | ValuationRequestOut | ListingRequestOut]
    total: int
    page: int
    page_size: int
    pages: int


def _paginate(query, db: Session, page: int, page_size: int) -> tuple[list, int]:
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all())
    return items, int(total)


def _build_query(model, status: LeadStatus | None, q: str | None):
    query = select(model).order_by(model.created_at.desc())
    if status:
        query = query.where(model.status == status)
    if q:
        term = f"%{q.strip().lower()}%"
        criteria = [
            func.lower(model.name).like(term),
            func.lower(model.email).like(term),
        ]
        if hasattr(model, "locality"):
            criteria.append(func.lower(model.locality).like(term))
        if hasattr(model, "message"):
            criteria.append(func.lower(model.message).like(term))
        query = query.where(or_(*criteria))
    return query


def _get_or_404(model, db: Session, record_id: int):
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"message": "Registro no encontrado."})
    return record


# ---------------------------------------------------------------------------
# Consultas (propiedades y generales)
# ---------------------------------------------------------------------------
@router.get("/inquiries", response_model=LeadPage, summary="Consultas recibidas")
def list_inquiries(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
    status: LeadStatus | None = Query(None),
    q: str | None = Query(None, max_length=80),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LeadPage:
    items, total = _paginate(_build_query(Inquiry, status, q), db, page, page_size)
    return LeadPage(
        items=[InquiryOut.model_validate(item, from_attributes=True) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.patch("/inquiries/{record_id}", response_model=InquiryOut, summary="Cambiar estado")
def update_inquiry(
    record_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> InquiryOut:
    record = _get_or_404(Inquiry, db, record_id)
    record.status = payload.status
    if payload.status == LeadStatus.ANSWERED:
        from app.models.common import utcnow

        record.answered_at = utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)
    return InquiryOut.model_validate(record, from_attributes=True)


@router.post(
    "/inquiries/{record_id}/notes", response_model=NoteOut, status_code=201,
    summary="Agregar nota interna",
)
def add_inquiry_note(
    record_id: int,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
) -> NoteOut:
    record = _get_or_404(Inquiry, db, record_id)
    note = InternalNote(inquiry_id=record.id, body=payload.body, author_id=user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note, from_attributes=True)


# ---------------------------------------------------------------------------
# Tasaciones
# ---------------------------------------------------------------------------
@router.get(
    "/valuation-requests", response_model=LeadPage, summary="Solicitudes de tasación"
)
def list_valuations(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
    status: LeadStatus | None = Query(None),
    q: str | None = Query(None, max_length=80),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LeadPage:
    items, total = _paginate(_build_query(ValuationRequest, status, q), db, page, page_size)
    return LeadPage(
        items=[ValuationRequestOut.model_validate(item, from_attributes=True) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.patch(
    "/valuation-requests/{record_id}", response_model=ValuationRequestOut, summary="Cambiar estado"
)
def update_valuation(
    record_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> ValuationRequestOut:
    record = _get_or_404(ValuationRequest, db, record_id)
    record.status = payload.status
    db.add(record)
    db.commit()
    db.refresh(record)
    return ValuationRequestOut.model_validate(record, from_attributes=True)


@router.post(
    "/valuation-requests/{record_id}/notes",
    response_model=NoteOut,
    status_code=201,
    summary="Agregar nota interna",
)
def add_valuation_note(
    record_id: int,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
) -> NoteOut:
    _get_or_404(ValuationRequest, db, record_id)
    note = InternalNote(valuation_id=record_id, body=payload.body, author_id=user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note, from_attributes=True)


# ---------------------------------------------------------------------------
# Solicitudes de publicación
# ---------------------------------------------------------------------------
@router.get(
    "/listing-requests", response_model=LeadPage, summary="Solicitudes de publicación"
)
def list_listings(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
    status: LeadStatus | None = Query(None),
    q: str | None = Query(None, max_length=80),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LeadPage:
    items, total = _paginate(_build_query(ListingRequest, status, q), db, page, page_size)
    return LeadPage(
        items=[ListingRequestOut.model_validate(item, from_attributes=True) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.patch(
    "/listing-requests/{record_id}", response_model=ListingRequestOut, summary="Cambiar estado"
)
def update_listing(
    record_id: int,
    payload: LeadStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> ListingRequestOut:
    record = _get_or_404(ListingRequest, db, record_id)
    record.status = payload.status
    db.add(record)
    db.commit()
    db.refresh(record)
    return ListingRequestOut.model_validate(record, from_attributes=True)


@router.post(
    "/listing-requests/{record_id}/notes",
    response_model=NoteOut,
    status_code=201,
    summary="Agregar nota interna",
)
def add_listing_note(
    record_id: int,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
) -> NoteOut:
    _get_or_404(ListingRequest, db, record_id)
    note = InternalNote(listing_id=record_id, body=payload.body, author_id=user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note, from_attributes=True)
