"""Esquemas Pydantic (contratos de la API) de ALMATE Propiedades."""

from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.schemas.lead import (
    InquiryCreate,
    InquiryOut,
    LeadStatusUpdate,
    ListingRequestCreate,
    ListingRequestOut,
    NoteCreate,
    NoteOut,
    ValuationRequestCreate,
    ValuationRequestOut,
)
from app.schemas.property import (
    PropertyAdminOut,
    PropertyCreate,
    PropertyDetailOut,
    PropertyImageAdminOut,
    PropertyImageOut,
    PropertySummaryOut,
    PropertyUpdate,
    PublicFilters,
)
from app.schemas.settings import PublicSettingsOut, SettingsUpdate

__all__ = [
    "InquiryCreate",
    "InquiryOut",
    "LeadStatusUpdate",
    "ListingRequestCreate",
    "ListingRequestOut",
    "LoginRequest",
    "NoteCreate",
    "NoteOut",
    "PropertyAdminOut",
    "PropertyCreate",
    "PropertyDetailOut",
    "PropertyImageAdminOut",
    "PropertyImageOut",
    "PropertySummaryOut",
    "PropertyUpdate",
    "PublicFilters",
    "PublicSettingsOut",
    "SettingsUpdate",
    "TokenResponse",
    "UserOut",
    "ValuationRequestCreate",
    "ValuationRequestOut",
]
