"""Carga de datos de demostración (idempotente).

* Descarga las fotografías del manifiesto `app/seed_images.json` a
  `backend/app/static/seed/` (sólo si todavía no están).
* Inserta propiedades ficticias de zonas del sur del Gran Buenos Aires.
* Inserta consultas y solicitudes de ejemplo para que el panel no esté vacío.

Todo lo que crea este módulo es **ficticio** y está claramente identificado
como datos de demostración (`ALM-Dnn-YY`).
"""

from __future__ import annotations

import logging
import shutil
import urllib.request
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.lead import (
    Inquiry,
    InquiryKind,
    ListingRequest,
    ValuationRequest,
)
from app.models.property import (
    DEFAULT_UNIT_BY_OPERATION,
    CommercialStatus,
    Operation,
    Property,
    PropertyImage,
    PropertyType,
    PublicationStatus,
)
from app.models.settings import BusinessSettings
from app.models.user import UserRole, User
from app.security import hash_password
from app.services.money import to_cents

logger = logging.getLogger("almate.seed")

USER_AGENT = "ALMATE-Propiedades-Demo/1.0 (datos de demostracion)"


# ---------------------------------------------------------------------------
# 1. Fotografías
# ---------------------------------------------------------------------------
def _manifest_path() -> Path:
    return Path(__file__).resolve().parents[1] / "seed_images.json"


def download_seed_images() -> dict[str, str]:
    """Descarga (una sola vez) las imágenes del manifiesto a `static/seed/`.

    Devuelve `{clave: "seed/<archivo>"}` con las rutas relativas al directorio
    estático. Si una descarga falla, se omite esa imagen sin cortar la carga.
    """
    settings = get_settings()
    manifest_file = _manifest_path()
    if not manifest_file.exists():
        logger.warning("No existe %s; la demo quedará sin fotografías.", manifest_file)
        return {}

    import json

    entries = json.loads(manifest_file.read_text(encoding="utf-8"))
    target_dir = settings.seed_images_path
    target_dir.mkdir(parents=True, exist_ok=True)

    available: dict[str, str] = {}
    for entry in entries:
        key = entry["key"]
        filename = f"{key}.jpg"
        destination = target_dir / filename
        if not destination.exists() or destination.stat().st_size == 0:
            try:
                request = urllib.request.Request(
                    entry["url"], headers={"User-Agent": USER_AGENT}
                )
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read()
                destination.write_bytes(data)
                logger.info("Imagen descargada: %s", filename)
            except Exception as exc:  # noqa: BLE001 - la demo sigue sin esa foto
                logger.warning("No se pudo descargar %s: %s", key, exc)
                continue
        available[key] = f"seed/{filename}"
    return available


def _attach_image(db: Session, prop: Property, relative_path: str, order: int) -> None:
    """Copia la foto de demo a la carpeta de la propiedad y registra la fila."""
    settings = get_settings()
    source = settings.upload_path.parent / relative_path
    if not source.exists():
        return

    folder = settings.upload_path / "properties" / prop.id
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / source.name
    if not destination.exists():
        shutil.copyfile(source, destination)

    storage_path = f"uploads/properties/{prop.id}/{source.name}"
    db.add(
        PropertyImage(
            property_id=prop.id,
            storage_path=storage_path,
            filename=source.name,
            alt_text=f"Fotografía {order + 1} de {prop.title}",
            is_main=order == 0,
            sort_order=order,
            mime_type="image/jpeg",
            size_bytes=destination.stat().st_size,
        )
    )


# ---------------------------------------------------------------------------
# 2. Propiedades ficticias
# ---------------------------------------------------------------------------
P = PropertyType
OP = Operation

DEMO_PROPERTIES: list[dict] = [
    {
        "code": "ALM-D01-26",
        "title": "Departamento 3 ambientes con balcón en Quilmes Centro",
        "description": (
            "Departamento en el corazón de Quilmes, a metros de la avenida Calchaquí y del "
            "predio ferial. Living comedor con balcón orientado al norte, cocina independiente "
            "equipada, dos dormitorios con placard, baño completo y toilette. Edificio con "
            "ascensor, portería y expensas administradas. Apto profesional."
        ),
        "operation": OP.BUY,
        "property_type": P.APARTMENT,
        "price": "92000.00",
        "currency": "USD",
        "expenses": "320.00",
        "commercial_status": CommercialStatus.AVAILABLE,
        "publication_status": PublicationStatus.PUBLISHED,
        "is_featured": True,
        "locality": "Quilmes",
        "neighborhood": "Centro",
        "department": "Quilmes",
        "address": "Av. Calchaquí 1200",
        "rooms": 4,
        "bedrooms": 2,
        "bathrooms": 1,
        "toilets": 1,
        "garages": 1,
        "surface_covered": "68.00",
        "surface_total": "74.00",
        "apto_professional": True,
        "services": ["Agua caliente", "Gas natural", "Calefacción", "Ascensor", "Portería"],
        "images": ["living-1", "kitchen-1", "bedroom-1"],
    },
    {
        "code": "ALM-D02-26",
        "title": "Departamento 2 ambientes reciclado en Quilmes Oeste",
        "description": (
            "Monoambiente independiente con ambiente separado, recién renovado: pisos, "
            "cocina y baño en excelente estado. Muy luminoso, con vista a interior de manzana. "
            "Ideal para primera vivienda o inversión."
        ),
        "operation": OP.BUY,
        "property_type": P.APARTMENT,
        "price": "68500.00",
        "currency": "USD",
        "expenses": "180.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Quilmes",
        "neighborhood": "Quilmes Oeste",
        "department": "Quilmes",
        "address": "Rivadavia 2400",
        "rooms": 2,
        "bedrooms": 1,
        "bathrooms": 1,
        "surface_covered": "45.00",
        "surface_total": "45.00",
        "services": ["Agua caliente", "Gas natural"],
        "images": ["living-2", "detail-1"],
    },
    {
        "code": "ALM-D03-26",
        "title": "Casa 4 ambientes con patio en Bernal",
        "description": (
            "Casa en Bernal sobre lote de 12 × 25 m, con living amplio, cocina comedor, tres "
            "dormitorios y dos baños. Patio con parrilla y una dependence al frente. "
            "A pocos cuadras del tren y de comercios."
        ),
        "operation": OP.BUY,
        "property_type": P.HOUSE,
        "price": "128000.00",
        "currency": "USD",
        "publication_status": PublicationStatus.PUBLISHED,
        "is_featured": True,
        "locality": "Bernal",
        "neighborhood": "Villa Antigua",
        "department": "Quilmes",
        "address": "Mitre 950",
        "rooms": 5,
        "bedrooms": 3,
        "bathrooms": 2,
        "garages": 1,
        "surface_covered": "110.00",
        "surface_semicovered": "22.00",
        "surface_total": "300.00",
        "antiquity_years": 18,
        "services": ["Agua caliente", "Gas natural", "Parrilla", "Pozo de agua"],
        "images": ["house-1", "garden-2", "living-3"],
    },
    {
        "code": "ALM-D04-26",
        "title": "PH luminoso con parrilla en Ezpeleta",
        "description": (
            "PH de dos dormitorios en planta alta, con living-comedor, cocina americana y "
            "patio propio con parrilla. Docena de unidades, expensas bajas y excelente "
            "conectividad con la avenida Calchaquí."
        ),
        "operation": OP.BUY,
        "property_type": P.PH,
        "price": "79000.00",
        "currency": "USD",
        "expenses": "95.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Ezpeleta",
        "neighborhood": "Ezpeleta Oeste",
        "department": "Quilmes",
        "address": "Los Aromos 480",
        "rooms": 3,
        "bedrooms": 2,
        "bathrooms": 1,
        "surface_covered": "78.00",
        "surface_total": "145.00",
        "services": ["Agua caliente", "Gas natural", "Parrilla"],
        "images": ["house-2", "detail-2"],
    },
    {
        "code": "ALM-D05-26",
        "title": "Departamento 3 ambientes a estrenar en Wilde",
        "description": (
            "Unidad nueva de estreno en edificio de pocas plantas. Dos dormitorios con "
            "placard, baño completo, cocina integrada y balcón. Cerca de la estación Wilde y "
            "del corredor verde."
        ),
        "operation": OP.BUY,
        "property_type": P.APARTMENT,
        "price": "88000.00",
        "currency": "USD",
        "expenses": "260.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Wilde",
        "neighborhood": "Wilde Centro",
        "department": "Avellaneda",
        "address": "Los Andes 1350",
        "rooms": 4,
        "bedrooms": 2,
        "bathrooms": 1,
        "garages": 1,
        "surface_covered": "62.00",
        "surface_total": "66.00",
        "apto_professional": True,
        "services": ["Agua caliente", "Gas natural", "Ascensor", "Portería"],
        "images": ["bedroom-2", "kitchen-2"],
    },
    {
        "code": "ALM-D06-26",
        "title": "Casa quinta con jardín en Don Bosco",
        "description": (
            "Casa quinta sobre lote de 500 m² con jardín amplio, parrilla techada y aljibe. "
            "Cuatro dormitorios, dos baños, living comedor y cocina equipada. Barrio tranquilo "
            "y arbolado, a metros del acceso."
        ),
        "operation": OP.BUY,
        "property_type": P.HOUSE,
        "price": "165000.00",
        "currency": "USD",
        "publication_status": PublicationStatus.PUBLISHED,
        "is_featured": True,
        "locality": "Don Bosco",
        "neighborhood": "Barrio Don Bosco",
        "department": "Quilmes",
        "address": "Calle 6 1250",
        "rooms": 6,
        "bedrooms": 4,
        "bathrooms": 2,
        "garages": 2,
        "surface_covered": "160.00",
        "surface_semicovered": "35.00",
        "surface_total": "500.00",
        "antiquity_years": 12,
        "services": ["Agua caliente", "Gas natural", "Parrilla", "Aljibe", "Jardín"],
        "images": ["house-3", "garden-3", "kitchen-3"],
    },
    {
        "code": "ALM-D07-26",
        "title": "Terreno de 900 m² en Berazategui",
        "description": (
            "Lote regular y plano de 900 m² en zona en crecimiento, con frente de 30 metros y "
            "todos los servicios en vereda. Escritura a la vista y posibilidad de fraccionamiento."
        ),
        "operation": OP.BUY,
        "property_type": P.LAND,
        "price": "45000.00",
        "currency": "USD",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Berazategui",
        "neighborhood": "Villafox",
        "department": "Berazategui",
        "address": "Ruta 14 km 5",
        "surface_total": "900.00",
        "services": ["Agua", "Gas natural", "Cloaca"],
        "images": ["land-1", "land-2"],
    },
    {
        "code": "ALM-D08-26",
        "title": "Local comercial con vitrina en Quilmes Centro",
        "description": (
            "Local en planta baja sobre avenida de alto tránsito, con vitrina de 6 metros, "
            "dependencias sanitarias y fondo de 20 m². Ideal para comercio, consultorio o "
            "estudio. Apto profesional."
        ),
        "operation": OP.BUY,
        "property_type": P.COMMERCIAL,
        "price": "78000.00",
        "currency": "USD",
        "expenses": "450.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Quilmes",
        "neighborhood": "Centro",
        "department": "Quilmes",
        "address": "San Martín 800",
        "surface_covered": "95.00",
        "surface_total": "95.00",
        "apto_professional": True,
        "services": ["Agua caliente", "Gas natural", "Aire acondicionado"],
        "images": ["storefront-1", "detail-3"],
    },
    {
        "code": "ALM-D09-26",
        "title": "Departamento 2 ambientes amoblado en alquiler, Quilmes Centro",
        "description": (
            "Departamento amoblado listo para habitar, a dos cuadras del tren. Incluye ropa de "
            "cama, muebles y electrodomésticos. Expensas y servicios por separado. Se piden "
            "meses de garantía."
        ),
        "operation": OP.RENT,
        "property_type": P.APARTMENT,
        "price": "380000.00",
        "currency": "ARS",
        "expenses": "60000.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "is_featured": True,
        "locality": "Quilmes",
        "neighborhood": "Centro",
        "department": "Quilmes",
        "address": "Colón 620",
        "rooms": 3,
        "bedrooms": 1,
        "bathrooms": 1,
        "surface_covered": "48.00",
        "surface_total": "48.00",
        "services": ["Agua caliente", "Gas natural", "Amoblado", "Internet"],
        "images": ["bedroom-3", "bathroom-1"],
    },
    {
        "code": "ALM-D10-26",
        "title": "Departamento 3 ambientes con balcón en alquiler, Wilde",
        "description": (
            "Alquiler mensual de tres ambientes en edificio con ascensor y patio. Dos "
            "dormitorios con placard, baño completo, cocina equipada y balcón con vista al "
            "interior. A estación Wilde caminando."
        ),
        "operation": OP.RENT,
        "property_type": P.APARTMENT,
        "price": "520000.00",
        "currency": "ARS",
        "expenses": "95000.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Wilde",
        "neighborhood": "Wilde Oeste",
        "department": "Avellaneda",
        "address": "Av. Antártida Argentina 2100",
        "rooms": 4,
        "bedrooms": 2,
        "bathrooms": 1,
        "garages": 1,
        "surface_covered": "70.00",
        "surface_total": "70.00",
        "services": ["Agua caliente", "Gas natural", "Ascensor", "Patio"],
        "images": ["building-1", "bathroom-2"],
    },
    {
        "code": "ALM-D11-26",
        "title": "Casa 5 ambientes con jardín en alquiler, Bernal",
        "description": (
            "Casa familiar de alquiler con jardín, parrilla y dos cocheras techadas. Living "
            "comedor amplio, cocina independiente, cuatro dormitorios y dos baños. Se aceptan "
            "mascotas."
        ),
        "operation": OP.RENT,
        "property_type": P.HOUSE,
        "price": "890000.00",
        "currency": "ARS",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Bernal",
        "neighborhood": "Bernal Oeste",
        "department": "Quilmes",
        "address": "Av. Hipólito Yrigoyen 15200",
        "rooms": 6,
        "bedrooms": 4,
        "bathrooms": 2,
        "garages": 2,
        "surface_covered": "170.00",
        "surface_total": "420.00",
        "services": ["Agua caliente", "Gas natural", "Parrilla", "Jardín", "Cochera"],
        "images": ["garden-1", "living-3"],
    },
    {
        "code": "ALM-D12-26",
        "title": "Casa temporal con parrilla en Berazategui",
        "description": (
            "Alquiler por días, ideal para estadías cortas o workation. Tres dormitorios, dos "
            "baños, wifi, parrilla y jardín. Check-in flexible y limpieza incluida. El precio "
            "indicado es por noche."
        ),
        "operation": OP.TEMPORARY_RENT,
        "property_type": P.HOUSE,
        "price": "65000.00",
        "currency": "ARS",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Berazategui",
        "neighborhood": "Francisco Romero",
        "department": "Berazategui",
        "address": "Calle 12 480",
        "rooms": 5,
        "bedrooms": 3,
        "bathrooms": 2,
        "garages": 1,
        "surface_covered": "120.00",
        "surface_total": "360.00",
        "services": ["Wifi", "Parrilla", "Aire acondicionado", "Jardín", "Cochera"],
        "images": ["garden-2", "detail-1"],
    },
    {
        "code": "ALM-D13-26",
        "title": "Monoambiente amoblado para alquiler temporal en Quilmes",
        "description": (
            "Estudio amoblado en el centro de Quilmes, a pasos de la avenida. Cocina equipada, "
            "baño completo, cama queen y escritorio. Estadías mínimas de 7 noches. El precio "
            "indicado es por noche."
        ),
        "operation": OP.TEMPORARY_RENT,
        "property_type": P.APARTMENT,
        "price": "52000.00",
        "currency": "ARS",
        "expenses": "15000.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Quilmes",
        "neighborhood": "Centro",
        "department": "Quilmes",
        "address": "Independencia 480",
        "rooms": 2,
        "bedrooms": 1,
        "bathrooms": 1,
        "surface_covered": "38.00",
        "surface_total": "38.00",
        "services": ["Wifi", "Amoblado", "Aire acondicionado", "Ascensor"],
        "images": ["bedroom-1", "living-3", "kitchen-1"],
    },
    {
        "code": "ALM-D14-26",
        "title": "Emprendimiento Torres del Sur: departamentos de 1 y 2 ambientes",
        "description": (
            "Nuevo emprendimiento residencial de 12 plantas en Quilmes Oeste. Departamentos "
            "de 1 y 2 ambientes con balcón, cocheras opcionales y espacios verdes. Entrega "
            "programada en 18 meses. Valores de referencia sujetos a actualización."
        ),
        "operation": OP.BUY,
        "property_type": P.APARTMENT,
        "price": "78000.00",
        "currency": "USD",
        "publication_status": PublicationStatus.PUBLISHED,
        "is_featured": True,
        "is_development": True,
        "locality": "Quilmes",
        "neighborhood": "Quilmes Oeste",
        "department": "Quilmes",
        "address": "Av. Rolando 3200",
        "rooms": 3,
        "bedrooms": 1,
        "bathrooms": 1,
        "surface_covered": "42.00",
        "surface_total": "42.00",
        "services": ["Ascensor", "Portería", "Parrilla", "Área verde", "Cochera"],
        "images": ["building-2", "building-3"],
    },
    {
        "code": "ALM-D15-26",
        "title": "Barrio cerrado Los Álamos: casas de 3 dormitorios",
        "description": (
            "Segunda etapa de un barrio cerrado con casas de 3 dormitorios, patio propio y "
            "acceso controlado. Modelos con y sin cocheras. Financiación en pesos y dólares "
            "coordinada con la desarrolladora. Imágenes ilustrativas del modelo."
        ),
        "operation": OP.BUY,
        "property_type": P.HOUSE,
        "price": "118000.00",
        "currency": "USD",
        "publication_status": PublicationStatus.PUBLISHED,
        "is_development": True,
        "locality": "Berazategui",
        "neighborhood": "Altos de San Francisco",
        "department": "Berazategui",
        "address": "Ruta Km 4.5",
        "rooms": 5,
        "bedrooms": 3,
        "bathrooms": 2,
        "garages": 1,
        "surface_covered": "98.00",
        "surface_total": "220.00",
        "services": ["Seguridad 24 hs", "Parrilla", "Área verde", "Cochera"],
        "images": ["building-3", "garden-2"],
    },
    {
        "code": "ALM-D16-26",
        "title": "Oficina de 80 m² en parque industrial",
        "description": (
            "Oficina diáfana en planta alta con tres puestos privados, sala de reuniones, "
            "baños y aire acondicionado central. Parque industrial con seguridad y transporte "
            "regular. Alquiler mensual más expensas."
        ),
        "operation": OP.RENT,
        "property_type": P.OFFICE,
        "price": "1200000.00",
        "currency": "ARS",
        "expenses": "180000.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Berazategui",
        "neighborhood": "Parque Industrial",
        "department": "Berazategui",
        "address": "Ruta 14 km 6",
        "rooms": 4,
        "bathrooms": 2,
        "garages": 2,
        "surface_covered": "80.00",
        "surface_total": "80.00",
        "apto_professional": True,
        "services": ["Aire acondicionado", "Seguridad 24 hs", "Internet"],
        "images": ["office-1", "detail-2"],
    },
    {
        "code": "ALM-D17-26",
        "title": "Cochera individual techada en Wilde",
        "description": (
            "Cochera individual con persiana automática y electricidad, en edificio con "
            "portería. Excelente opción de inversión o guardado en zona céntrica de Wilde."
        ),
        "operation": OP.BUY,
        "property_type": P.GARAGE,
        "price": "16500.00",
        "currency": "USD",
        "expenses": "75.00",
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Wilde",
        "neighborhood": "Wilde Centro",
        "department": "Avellaneda",
        "address": "Los Aromos 900",
        "surface_covered": "18.00",
        "surface_total": "18.00",
        "services": ["Persiana automática", "Portería"],
        "images": ["garage-1"],
    },
    {
        "code": "ALM-D18-26",
        "title": "Departamento 4 ambientes en Bernal Oeste",
        "description": (
            "Amplio departamento de cuatro ambientes con dos dormitorios, dos baños, "
            "living-comedor con balcón y cocheras. Se encuentra reservado a la espera de la "
            "señatura."
        ),
        "operation": OP.BUY,
        "property_type": P.APARTMENT,
        "price": "103000.00",
        "currency": "USD",
        "expenses": "410.00",
        "commercial_status": CommercialStatus.RESERVED,
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Bernal",
        "neighborhood": "Bernal Oeste",
        "department": "Quilmes",
        "address": "Av. Nazca 480",
        "rooms": 5,
        "bedrooms": 3,
        "bathrooms": 2,
        "garages": 1,
        "surface_covered": "96.00",
        "surface_total": "102.00",
        "services": ["Agua caliente", "Gas natural", "Ascensor", "Cochera"],
        "images": ["living-3", "bathroom-3"],
    },
    {
        "code": "ALM-D19-26",
        "title": "Casa vendida en Ezpeleta",
        "description": (
            "Casa de tres dormitorios con patio, vendida en el mes de agosto. Se mantiene "
            "publicada como referencia de operaciones cerradas por el estudio."
        ),
        "operation": OP.BUY,
        "property_type": P.HOUSE,
        "price": "98000.00",
        "currency": "USD",
        "commercial_status": CommercialStatus.SOLD,
        "publication_status": PublicationStatus.PUBLISHED,
        "locality": "Ezpeleta",
        "neighborhood": "Ezpeleta Norte",
        "department": "Quilmes",
        "address": "Sarmiento 1300",
        "rooms": 4,
        "bedrooms": 3,
        "bathrooms": 1,
        "surface_covered": "88.00",
        "surface_total": "210.00",
        "services": ["Agua caliente", "Gas natural", "Parrilla"],
        "images": ["detail-2", "garden-3"],
    },
    {
        "code": "ALM-D20-26",
        "title": "Estudio profesional en Quilmes (borrador)",
        "description": (
            "Borrador de publicación: estudio de 30 m² en planta baja apto para consultorio. "
            "Pendiente completar fotografías y precio definitivo."
        ),
        "operation": OP.BUY,
        "property_type": P.OFFICE,
        "publication_status": PublicationStatus.DRAFT,
        "locality": "Quilmes",
        "neighborhood": "Centro",
        "department": "Quilmes",
        "address": "Moreno 600",
        "surface_covered": "30.00",
        "apto_professional": True,
        "services": ["Aire acondicionado"],
        "images": ["garage-2"],
    },
    {
        "code": "ALM-D21-26",
        "title": "Departamento archivado en Avellaneda",
        "description": (
            "Publicación archivada a pedido del propietario. No se muestra en el catálogo "
            "público."
        ),
        "operation": OP.RENT,
        "property_type": P.APARTMENT,
        "price": "300000.00",
        "currency": "ARS",
        "publication_status": PublicationStatus.ARCHIVED,
        "locality": "Avellaneda",
        "neighborhood": "Dock Sud",
        "department": "Avellaneda",
        "address": "Av. Presidente Mitre 1500",
        "rooms": 3,
        "bedrooms": 1,
        "bathrooms": 1,
        "surface_covered": "42.00",
        "images": ["garage-3"],
    },
]


def _seed_properties(db: Session, images: dict[str, str]) -> int:
    """Inserta las propiedades ficticias que todavía no existen (por código)."""
    from app.models.common import utcnow

    created = 0
    for source in DEMO_PROPERTIES:
        data = dict(source)
        code = data["code"]
        image_keys = data.pop("images", [])
        price = data.pop("price", None)
        expenses = data.pop("expenses", None)
        data.setdefault("antiquity_years", 5)
        operation = data["operation"]
        is_published = data["publication_status"] == PublicationStatus.PUBLISHED

        prop = db.scalar(select(Property).where(Property.code == code))
        if prop is None:
            prop = Property(
                **data,
                price_cents=to_cents(price),
                expenses_cents=to_cents(expenses),
                price_unit=DEFAULT_UNIT_BY_OPERATION[operation],
                published_at=utcnow() if is_published else None,
            )
            db.add(prop)
            db.flush()
            created += 1

        # Adjunta las fotografías que todavía no estén registradas (permite
        # completar la demo si la descarga de imágenes se hizo en varios pasos).
        attached = {image.filename for image in prop.images}
        order = max((image.sort_order for image in prop.images), default=-1) + 1
        for key in image_keys:
            relative = images.get(key)
            if not relative or Path(relative).name in attached:
                continue
            _attach_image(db, prop, relative, order)
            attached.add(Path(relative).name)
            order += 1

    db.commit()
    return created


# ---------------------------------------------------------------------------
# 3. Leads de ejemplo (panel)
# ---------------------------------------------------------------------------
def _seed_leads(db: Session) -> int:
    if db.scalar(select(func.count(Inquiry.id))) or 0:
        return 0  # ya hay consultas: no duplicar
    if db.scalar(select(func.count(ValuationRequest.id))) or 0:
        return 0

    prop = db.scalar(select(Property).where(Property.code == "ALM-D01-26"))
    demo_rows = [
        Inquiry(
            kind=InquiryKind.PROPERTY,
            property_id=prop.id if prop else None,
            property_code=prop.code if prop else None,
            property_title=prop.title if prop else None,
            name="Marina Sosa",
            email="marina.sosa@ejemplo.com",
            phone="+54 11 2233-4455",
            message="Hola, me interesa el departamento de Quilmes Centro. ¿Se puede visitar el sábado a la mañana?",
        ),
        Inquiry(
            kind=InquiryKind.GENERAL,
            name="Javier Ríos",
            email="javier.rios@ejemplo.com",
            phone="+54 11 6677-8899",
            message="Quisiera consultar por opciones de 3 ambientes en Quilmes o Bernal con presupuesto de USD 90.000.",
        ),
        Inquiry(
            kind=InquiryKind.GENERAL,
            name="Lucía Fernández",
            email="lucia.fernandez@ejemplo.com",
            message="Buenos días, ¿hacen administración de alquileres? Necesito que gestionen un contrato.",
        ),
        ValuationRequest(
            name="Rodrigo Peña",
            email="rodrigo.pena@ejemplo.com",
            phone="+54 11 4455-6677",
            property_type="house",
            operation="buy",
            locality="Bernal",
            neighborhood="Villa Antigua",
            surface_covered="110",
            bedrooms="3",
            message="Necesito tasar una casa para una operación de venta.",
        ),
        ValuationRequest(
            name="Norma Gómez",
            email="norma.gomez@ejemplo.com",
            property_type="apartment",
            operation="rent",
            locality="Wilde",
            surface_covered="70",
            bedrooms="2",
            message="Quiero saber cuánto podría alquilar mi departamento.",
        ),
        ListingRequest(
            name="Héctor Bianchi",
            email="hector.bianchi@ejemplo.com",
            phone="+54 11 7788-9900",
            operation="buy",
            property_type="house",
            locality="Don Bosco",
            neighborhood="Barrio Don Bosco",
            surface_covered="140",
            bedrooms="4",
            expected_price="USD 155.000",
            message="Quiero publicar mi casa, tiene jardín y parrilla.",
        ),
        ListingRequest(
            name="Sofía Acosta",
            email="sofia.acosta@ejemplo.com",
            operation="rent",
            property_type="apartment",
            locality="Quilmes",
            neighborhood="Centro",
            surface_covered="48",
            bedrooms="1",
            expected_price="ARS 350.000",
            message="Tengo un monoambiente amoblado para alquilar.",
        ),
    ]
    for row in demo_rows:
        db.add(row)
    db.commit()
    return len(demo_rows)


# ---------------------------------------------------------------------------
# 4. Punto de entrada
# ---------------------------------------------------------------------------
def run_seed(db: Session) -> dict[str, int]:
    """Carga completa. Idempotente: re-ejecutarla no duplica registros."""
    BusinessSettings.get_or_create(db)
    images = download_seed_images()
    properties = _seed_properties(db, images)
    leads = _seed_leads(db)

    total_images = int(db.scalar(select(func.count(PropertyImage.id))) or 0)
    return {
        "propiedades_nuevas": properties,
        "propiedades_total": int(db.scalar(select(func.count(Property.id))) or 0),
        "imagenes_disponibles": len(images),
        "imagenes_registradas": total_images,
        "leads_nuevos": leads,
    }


def ensure_demo_admin(db: Session, email: str, password: str, name: str) -> User:
    """Crea (o corrige) el usuario administrador de la demo."""
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None:
        user = User(
            email=email.lower().strip(),
            full_name=name,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
    else:
        user.password_hash = hash_password(password)
        user.role = UserRole.ADMIN
        user.is_active = True
    db.commit()
    db.refresh(user)
    return user
