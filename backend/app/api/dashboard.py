"""Métricas del panel: todas calculadas desde la base de datos."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_staff
from app.database import get_db
from app.models.lead import Inquiry, LeadStatus, ListingRequest, ValuationRequest
from app.models.property import CommercialStatus, Property, PublicationStatus
from app.models.user import User
from app.schemas.lead import InquiryOut
from app.schemas.property import PropertySummaryOut
from app.services import properties as service

router = APIRouter(prefix="/admin", tags=["Admin · Dashboard"])


class DashboardCounts(BaseModel):
    properties_total: int
    published: int
    draft: int
    archived: int
    available: int
    reserved: int
    sold: int
    rented: int
    inquiries_total: int
    inquiries_new: int
    valuations_pending: int
    listings_pending: int
    featured: int


class RecentProperty(BaseModel):
    code: str
    title: str
    publication_status: PublicationStatus
    commercial_status: CommercialStatus
    updated_at: str
    image: dict | None = None


class DashboardOut(BaseModel):
    counts: DashboardCounts
    inquiries_by_status: dict[str, int]
    last_inquiries: list[InquiryOut]
    last_properties: list[PropertySummaryOut]


def _count(db: Session, *criteria) -> int:
    query = select(func.count(Property.id))
    if criteria:
        query = query.where(*criteria)
    return int(db.scalar(query) or 0)


def _lead_count(db: Session, model, *criteria) -> int:
    query = select(func.count(model.id))
    if criteria:
        query = query.where(*criteria)
    return int(db.scalar(query) or 0)


@router.get("/dashboard", response_model=DashboardOut, summary="Métricas del panel")
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_staff)) -> DashboardOut:
    pending = (LeadStatus.NEW, LeadStatus.FOLLOWING)

    counts = DashboardCounts(
        properties_total=_count(db),
        published=_count(db, Property.publication_status == PublicationStatus.PUBLISHED),
        draft=_count(db, Property.publication_status == PublicationStatus.DRAFT),
        archived=_count(db, Property.publication_status == PublicationStatus.ARCHIVED),
        available=_count(db, Property.commercial_status == CommercialStatus.AVAILABLE),
        reserved=_count(db, Property.commercial_status == CommercialStatus.RESERVED),
        sold=_count(db, Property.commercial_status == CommercialStatus.SOLD),
        rented=_count(db, Property.commercial_status == CommercialStatus.RENTED),
        inquiries_total=_lead_count(db, Inquiry),
        inquiries_new=_lead_count(db, Inquiry, Inquiry.status == LeadStatus.NEW),
        valuations_pending=_lead_count(db, ValuationRequest, ValuationRequest.status.in_(pending)),
        listings_pending=_lead_count(db, ListingRequest, ListingRequest.status.in_(pending)),
        featured=_count(db, Property.is_featured.is_(True)),
    )

    status_rows = db.execute(
        select(Inquiry.status, func.count(Inquiry.id)).group_by(Inquiry.status)
    ).all()
    by_status = {status.value: 0 for status in LeadStatus}
    by_status.update({row[0].value if hasattr(row[0], "value") else str(row[0]): int(row[1]) for row in status_rows})

    last_inquiries = list(
        db.scalars(select(Inquiry).order_by(Inquiry.created_at.desc()).limit(5)).all()
    )
    last_properties = list(
        db.scalars(
            service.base_property_query().order_by(Property.updated_at.desc()).limit(5)
        ).all()
    )

    return DashboardOut(
        counts=counts,
        inquiries_by_status=by_status,
        last_inquiries=[InquiryOut.model_validate(i, from_attributes=True) for i in last_inquiries],
        last_properties=[service.to_summary(p) for p in last_properties],
    )
