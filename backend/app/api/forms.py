"""Formularios públicos: consultas, tasaciones y publicación de propiedades.

Todos los datos se validan en el servidor y se persisten en la base de datos;
la confirmación se devuelve sólo después de confirmar la transacción.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lead import (
    Inquiry,
    InquiryKind,
    ListingRequest,
    ValuationRequest,
)
from app.models.property import Property, PublicationStatus
from app.schemas.lead import (
    AcceptedResponse,
    InquiryCreate,
    ListingRequestCreate,
    ValuationRequestCreate,
)
from app.services.ratelimit import form_limiter, inquiry_limiter

router = APIRouter(tags=["Formularios públicos"])

GENERAL_MESSAGE = (
    "Recibimos tu consulta. Te vamos a responder a la brevedad al correo que nos dejaste."
)
VALUATION_MESSAGE = (
    "Solicitud de tasación registrada. Un asesor se va a poner en contacto con vos."
)
LISTING_MESSAGE = (
    "Recibimos los datos de tu propiedad. Te contactamos a la brevedad para coordinar una visita."
)


def _resolve_property(db: Session, code: str | None) -> Property | None:
    """Sólo se pueden consultar propiedades publicadas (nunca borradores)."""
    if not code:
        return None
    prop = db.scalar(
        select(Property).where(
            Property.code == code.upper().strip(),
            Property.publication_status == PublicationStatus.PUBLISHED,
        )
    )
    if prop is None:
        raise HTTPException(
            status_code=422,
            detail={"message": "La propiedad indicada no existe o ya no está publicada."},
        )
    return prop


def _email(value: str) -> str:
    return value.strip().lower()


@router.post(
    "/inquiries",
    response_model=AcceptedResponse,
    status_code=201,
    summary="Consulta por una propiedad o consulta general",
)
def create_inquiry(
    payload: InquiryCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> AcceptedResponse:
    inquiry_limiter.check_request(request, "inquiry")

    prop = _resolve_property(db, payload.property_code)

    inquiry = Inquiry(
        kind=InquiryKind.PROPERTY if prop is not None else InquiryKind.GENERAL,
        property_id=prop.id if prop else None,
        property_code=prop.code if prop else None,
        property_title=prop.title if prop else None,
        name=payload.name.strip(),
        email=_email(payload.email),
        phone=payload.phone,
        message=payload.message.strip(),
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return AcceptedResponse(ok=True, message=GENERAL_MESSAGE, id=inquiry.id)


@router.post(
    "/valuation-requests",
    response_model=AcceptedResponse,
    status_code=201,
    summary="Solicitud de tasación",
)
def create_valuation(
    payload: ValuationRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> AcceptedResponse:
    form_limiter.check_request(request, "valuation")

    from app.models.lead import ValuationRequest

    record = ValuationRequest(
        name=payload.name.strip(),
        email=_email(payload.email),
        phone=payload.phone,
        property_type=payload.property_type.strip(),
        operation=payload.operation.strip() if payload.operation else None,
        locality=payload.locality.strip(),
        neighborhood=payload.neighborhood.strip() if payload.neighborhood else None,
        surface_covered=payload.surface_covered,
        bedrooms=payload.bedrooms,
        message=payload.message.strip() if payload.message else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return AcceptedResponse(ok=True, message=VALUATION_MESSAGE, id=record.id)


@router.post(
    "/listing-requests",
    response_model=AcceptedResponse,
    status_code=201,
    summary="Solicitud de publicación / oferta de propiedad",
)
def create_listing_request(
    payload: ListingRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> AcceptedResponse:
    form_limiter.check_request(request, "listing")

    from app.models.lead import ListingRequest

    record = ListingRequest(
        name=payload.name.strip(),
        email=_email(payload.email),
        phone=payload.phone,
        operation=payload.operation.strip(),
        property_type=payload.property_type.strip(),
        locality=payload.locality.strip(),
        neighborhood=payload.neighborhood.strip() if payload.neighborhood else None,
        surface_covered=payload.surface_covered,
        bedrooms=payload.bedrooms,
        expected_price=payload.expected_price,
        message=payload.message.strip() if payload.message else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return AcceptedResponse(ok=True, message=LISTING_MESSAGE, id=record.id)
