"""Alta, validación y borrado de fotografías de propiedades.

Medidas de seguridad aplicadas:

* límite de tamaño configurable (`MAX_UPLOAD_MB`);
* validación real del contenido con Pillow (no se confía en la extensión ni en
  el `Content-Type` declarado por el navegador);
* nombres de archivo generados por el servidor (UUID + extensión canónica),
  sin nombres del cliente;
* las rutas se resuelven y verifican contra el directorio de subidas para
  evitar *path traversal*;
* al borrar la fila también se borra el archivo, y viceversa: si el archivo no
  existe, la fila se elimina igualmente para no dejar referencias rotas.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.property import Property, PropertyImage

EXTENSIONS_BY_FORMAT = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


class ImageError(Exception):
    """Error de validación de imagen (se traduce a HTTP 400/413)."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _validate_and_read(data: bytes) -> tuple[bytes, str, str]:
    """Devuelve (bytes, extensión, mime) si el contenido es una imagen válida."""
    settings = get_settings()
    if not data:
        raise ImageError("El archivo está vacío.")
    if len(data) > settings.max_upload_bytes:
        raise ImageError(
            f"La imagen supera el máximo de {settings.max_upload_mb} MB.", status_code=413
        )
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()  # valida estructura interna
        with Image.open(io.BytesIO(data)) as img:
            fmt = (img.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageError("El archivo no es una imagen válida.") from exc

    if fmt not in EXTENSIONS_BY_FORMAT:
        raise ImageError("Formato no permitido. Usá JPG, PNG o WebP.")

    ext = EXTENSIONS_BY_FORMAT[fmt]
    mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[fmt]
    return data, ext, mime


def _safe_path(storage_path: str) -> Path:
    """Resuelve una ruta de almacenamiento y verifica que esté dentro de `static/`."""
    settings = get_settings()
    static_root = (settings.upload_path.parent).resolve()
    target = (static_root / storage_path.lstrip("/")).resolve()
    if not str(target).startswith(str(static_root)):
        raise ImageError("Ruta de imagen inválida.", status_code=400)
    return target


def next_order(db: Session, property_id: str) -> int:
    current = db.scalar(
        select(func.max(PropertyImage.sort_order)).where(
            PropertyImage.property_id == property_id
        )
    )
    return int(current + 1) if current is not None else 0


def save_property_image(
    db: Session,
    prop: Property,
    data: bytes,
    *,
    alt_text: str = "",
    filename_hint: str | None = None,
    make_main: bool = False,
) -> PropertyImage:
    """Valida, almacena y registra una fotografía en la base de datos."""
    settings = get_settings()

    count = db.scalar(
        select(func.count(PropertyImage.id)).where(PropertyImage.property_id == prop.id)
    ) or 0
    if count >= settings.max_images_per_property:
        raise ImageError(
            f"Una propiedad puede tener hasta {settings.max_images_per_property} fotografías.",
            status_code=400,
        )

    data, ext, mime = _validate_and_read(data)

    folder = Path("uploads") / "properties" / prop.id
    absolute_folder = settings.upload_path / "properties" / prop.id
    absolute_folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    (absolute_folder / filename).write_bytes(data)

    image = PropertyImage(
        property_id=prop.id,
        storage_path=f"{folder.as_posix()}/{filename}",
        filename=filename,
        alt_text=(alt_text or "").strip()[:200],
        sort_order=next_order(db, prop.id),
        mime_type=mime,
        size_bytes=len(data),
        is_main=make_main,
    )
    db.add(image)
    db.flush()

    # La primera fotografía siempre es la principal.
    if make_main or count == 0:
        set_main_image(db, image)
    db.flush()
    return image


def set_main_image(db: Session, image: PropertyImage) -> None:
    """Marca `image` como principal de su propiedad."""
    others = db.scalars(
        select(PropertyImage).where(
            PropertyImage.property_id == image.property_id,
            PropertyImage.id != image.id,
        )
    ).all()
    for other in others:
        other.is_main = False
    image.is_main = True
    db.flush()


def reorder_images(db: Session, property_id: str, ordered_ids: list[int]) -> list[PropertyImage]:
    """Reordena las imágenes según la lista de ids recibida."""
    images = db.scalars(
        select(PropertyImage).where(PropertyImage.property_id == property_id)
    ).all()
    by_id = {img.id: img for img in images}
    if not ordered_ids or set(ordered_ids) != set(by_id):
        raise ImageError("El orden recibido no coincide con las imágenes de la propiedad.")
    for position, image_id in enumerate(ordered_ids):
        by_id[image_id].sort_order = position
    db.flush()
    return [by_id[i] for i in ordered_ids]


def delete_image(db: Session, image: PropertyImage) -> None:
    """Elimina el archivo y la fila (sin dejar referencias rotas)."""
    try:
        path = _safe_path(image.storage_path)
        if path.is_file():
            path.unlink()
    except OSError:
        # Si el archivo no se puede borrar, la fila igualmente se elimina:
        # la API nunca volverá a referenciar esa ruta.
        pass

    was_main = image.is_main
    property_id = image.property_id
    db.delete(image)
    db.flush()

    if was_main:
        replacement = db.scalar(
            select(PropertyImage)
            .where(PropertyImage.property_id == property_id)
            .order_by(PropertyImage.sort_order, PropertyImage.id)
        )
        if replacement is not None:
            replacement.is_main = True
            db.flush()


def delete_property_files(prop: Property) -> None:
    """Borra del disco todas las fotografías de una propiedad.

    Se usa antes de eliminar la propiedad: al borrar la fila (con `ON DELETE
    CASCADE`) las imágenes desaparecen de la base, por lo que los archivos
    deben limpiarse para no acumular huérfanos.
    """
    folder = get_settings().upload_path / "properties" / prop.id
    if folder.is_dir():
        for path in folder.iterdir():
            if path.is_file():
                try:
                    path.unlink()
                except OSError:
                    pass
        try:
            folder.rmdir()
        except OSError:
            pass
    for image in prop.images:
        try:
            target = _safe_path(image.storage_path)
            if target.is_file():
                target.unlink()
        except (ImageError, OSError):
            pass
