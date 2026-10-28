"""Gestión administrativa de fotografías (subida, orden, alt y borrado)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin_properties import get_property_or_404
from app.api.deps import require_staff
from app.config import get_settings
from app.database import get_db
from app.models.property import PropertyImage
from app.models.user import User
from app.schemas.property import PropertyImageAdminOut
from app.services import images as service

router = APIRouter(prefix="/admin", tags=["Admin · Fotografías"])


class ImagePatch(BaseModel):
    alt_text: str | None = Field(default=None, max_length=200)
    is_main: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=999)


class ReorderPayload(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=100)


def _images_response(db: Session, property_id: str) -> list[PropertyImageAdminOut]:
    rows = db.scalars(
        select(PropertyImage)
        .where(PropertyImage.property_id == property_id)
        .order_by(PropertyImage.sort_order, PropertyImage.id)
    ).all()
    return [
        PropertyImageAdminOut(
            id=img.id,
            url=img.url,
            alt=img.alt_text or "",
            is_main=img.is_main,
            sort_order=img.sort_order,
            filename=img.filename,
            mime_type=img.mime_type,
            size_bytes=img.size_bytes,
            created_at=img.created_at,
        )
        for img in rows
    ]


def _image_or_404(db: Session, property_id: str, image_id: int) -> PropertyImage:
    image = db.scalar(
        select(PropertyImage).where(
            PropertyImage.id == image_id, PropertyImage.property_id == property_id
        )
    )
    if image is None:
        raise HTTPException(status_code=404, detail={"message": "Fotografía no encontrada."})
    return image


@router.post(
    "/properties/{identifier}/images",
    response_model=list[PropertyImageAdminOut],
    status_code=status.HTTP_201_CREATED,
    summary="Subir fotografías (multipart/form-data)",
)
async def upload_images(
    identifier: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
    files: list[UploadFile] = File(..., description="Una o varias imágenes"),
    alt_text: str = Form("", max_length=200),
    make_main: bool = Form(False),
) -> list[PropertyImageAdminOut]:
    prop = get_property_or_404(db, identifier)
    try:
        for upload in files:
            data = await upload.read()
            service.save_property_image(
                db,
                prop,
                data,
                alt_text=alt_text,
                filename_hint=upload.filename,
                make_main=make_main,
            )
        db.commit()
    except service.ImageError as exc:
        db.rollback()
        raise HTTPException(
            status_code=exc.status_code, detail={"message": str(exc)}
        ) from exc
    except Exception:
        db.rollback()
        raise
    return _images_response(db, prop.id)


@router.patch(
    "/properties/{identifier}/images/{image_id}",
    response_model=list[PropertyImageAdminOut],
    summary="Actualizar texto alternativo o marcar como principal",
)
def update_image(
    identifier: str,
    image_id: int,
    payload: ImagePatch,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[PropertyImageAdminOut]:
    prop = get_property_or_404(db, identifier)
    image = _image_or_404(db, prop.id, image_id)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=422, detail={"message": "No se recibieron cambios para aplicar."}
        )

    if "alt_text" in data and data["alt_text"] is not None:
        image.alt_text = data["alt_text"].strip()
    if data.get("sort_order") is not None:
        image.sort_order = data["sort_order"]
    db.add(image)
    db.flush()

    if data.get("is_main"):
        service.set_main_image(db, image)
    db.commit()
    return _images_response(db, prop.id)


@router.post(
    "/properties/{identifier}/images/reorder",
    response_model=list[PropertyImageAdminOut],
    summary="Reordenar fotografías",
)
def reorder_images(
    identifier: str,
    payload: ReorderPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[PropertyImageAdminOut]:
    prop = get_property_or_404(db, identifier)
    try:
        service.reorder_images(db, prop.id, payload.ids)
        db.commit()
    except service.ImageError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail={"message": str(exc)}) from exc
    return _images_response(db, prop.id)


@router.delete(
    "/properties/{identifier}/images/{image_id}",
    response_model=list[PropertyImageAdminOut],
    summary="Eliminar fotografía (archivo y registro)",
)
def delete_image(
    identifier: str,
    image_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[PropertyImageAdminOut]:
    prop = get_property_or_404(db, identifier)
    image = _image_or_404(db, prop.id, image_id)
    service.delete_image(db, image)
    db.commit()
    return _images_response(db, prop.id)


@router.get(
    "/uploads-limit",
    summary="Límites de subida aplicados",
)
def upload_limits(_: User = Depends(require_staff)) -> dict:
    settings = get_settings()
    return {
        "max_upload_mb": settings.max_upload_mb,
        "max_images_per_property": settings.max_images_per_property,
        "allowed_types": list(settings.allowed_image_types),
    }
