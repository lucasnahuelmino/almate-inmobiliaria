"""Modelos ORM de ALMATE Propiedades.

Importar todos los módulos aquí garantiza que `Base.metadata` conozca
todas las tablas antes de crear el esquema o generar migraciones.
"""

from app.models.common import TimestampMixin, utcnow
from app.models.lead import (
    Inquiry,
    InquiryKind,
    InternalNote,
    LeadStatus,
    ListingRequest,
    ValuationRequest,
)
from app.models.property import (
    CommercialStatus,
    Operation,
    Property,
    PropertyImage,
    PropertyType,
    PublicationStatus,
)
from app.models.settings import DEFAULT_CREDIT, BusinessSettings
from app.models.user import User, UserRole

__all__ = [
    "BusinessSettings",
    "CommercialStatus",
    "DEFAULT_CREDIT",
    "Inquiry",
    "InquiryKind",
    "InternalNote",
    "LeadStatus",
    "ListingRequest",
    "Operation",
    "Property",
    "PropertyImage",
    "PropertyType",
    "PublicationStatus",
    "TimestampMixin",
    "User",
    "UserRole",
    "ValuationRequest",
    "utcnow",
]
