"""Gestión de fotografías: subida, validación, orden, principal y borrado."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import get_settings
from conftest import delete_property_record, make_property


def jpeg_bytes(width: int = 1200, height: int = 800, color=(200, 190, 170)) -> bytes:
    """Genera un JPEG válido en memoria (sin archivos auxiliares)."""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (300, 300), (120, 130, 116)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def property_with_images(admin_headers):
    prop = make_property(code="ALM-IMG-01", title="Propiedad con fotografías")
    yield prop
    delete_property_record("ALM-IMG-01")


def upload(client, code, files, headers, **data):
    return client.post(
        f"/api/admin/properties/{code}/images", files=files, data=data, headers=headers
    )


def test_subida_de_imagen_valida(client, admin_headers, property_with_images) -> None:
    response = upload(
        client,
        property_with_images.code,
        [("files", ("fachada.jpg", jpeg_bytes(), "image/jpeg"))],
        admin_headers,
        alt_text="Fachada principal",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0]["alt"] == "Fachada principal"
    assert body[0]["is_main"] is True
    assert body[0]["url"].startswith("/static/")
    assert body[0]["mime_type"] == "image/jpeg"
    assert body[0]["size_bytes"] > 0

    # El archivo quedó en disco y es accesible públicamente.
    image_url = body[0]["url"]
    assert client.get(image_url).status_code == 200


def test_archivo_no_imagen_rechazado(client, admin_headers, property_with_images) -> None:
    response = upload(
        client,
        property_with_images.code,
        [("files", ("malicioso.jpg", b"esto no es una imagen", "image/jpeg"))],
        admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["message"]
    # No se registró ninguna imagen.
    detail = client.get(
        f"/api/admin/properties/{property_with_images.code}", headers=admin_headers
    ).json()
    assert detail["images"] == []


def test_extension_disfrazada_rechazada(client, admin_headers, property_with_images) -> None:
    """Un .exe renombrado a .jpg no pasa la validación con Pillow."""
    response = upload(
        client,
        property_with_images.code,
        [("files", ("trojan.jpg", b"MZ\x90\x00 resto del binario", "image/jpeg"))],
        admin_headers,
    )
    assert response.status_code == 400


def test_varias_imagenes_en_una_sola_peticion(
    client, admin_headers, property_with_images
) -> None:
    response = upload(
        client,
        property_with_images.code,
        [
            ("files", ("una.jpg", jpeg_bytes(color=(10, 20, 30)), "image/jpeg")),
            ("files", ("dos.png", png_bytes(), "image/png")),
        ],
        admin_headers,
    )
    assert response.status_code == 201
    assert len(response.json()) == 2


def test_marcar_como_principal(client, admin_headers, property_with_images) -> None:
    code = property_with_images.code
    first = upload(
        client, code, [("files", ("a.jpg", jpeg_bytes(), "image/jpeg"))], admin_headers
    ).json()[0]
    second_upload = upload(
        client, code, [("files", ("b.jpg", jpeg_bytes(), "image/jpeg"))], admin_headers
    ).json()
    # La respuesta incluye todas las imágenes: la nueva es la que no estaba.
    second = next(item for item in second_upload if item["id"] != first["id"])

    assert first["is_main"] is True
    assert second["is_main"] is False

    updated = client.patch(
        f"/api/admin/properties/{code}/images/{second['id']}",
        json={"is_main": True},
        headers=admin_headers,
    ).json()
    by_id = {item["id"]: item for item in updated}
    assert by_id[second["id"]]["is_main"] is True
    assert by_id[first["id"]]["is_main"] is False


def test_actualizar_texto_alternativo(client, admin_headers, property_with_images) -> None:
    code = property_with_images.code
    image = upload(
        client, code, [("files", ("a.jpg", jpeg_bytes(), "image/jpeg"))], admin_headers
    ).json()[0]

    updated = client.patch(
        f"/api/admin/properties/{code}/images/{image['id']}",
        json={"alt_text": "Living con balcón"},
        headers=admin_headers,
    ).json()
    assert updated[0]["alt"] == "Living con balcón"


def test_patch_con_campos_desconocidos(client, admin_headers, property_with_images) -> None:
    code = property_with_images.code
    image = upload(
        client, code, [("files", ("a.jpg", jpeg_bytes(), "image/jpeg"))], admin_headers
    ).json()[0]
    response = client.patch(
        f"/api/admin/properties/{code}/images/{image['id']}",
        json={"storage_path": "../../etc/passwd"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_reordenar_imagenes(client, admin_headers, property_with_images) -> None:
    code = property_with_images.code
    images = upload(
        client,
        code,
        [
            ("files", ("a.jpg", jpeg_bytes(), "image/jpeg")),
            ("files", ("b.jpg", jpeg_bytes(), "image/jpeg")),
            ("files", ("c.jpg", jpeg_bytes(), "image/jpeg")),
        ],
        admin_headers,
    ).json()
    ids = [item["id"] for item in images]
    reversed_ids = list(reversed(ids))

    response = client.post(
        f"/api/admin/properties/{code}/images/reorder",
        json={"ids": reversed_ids},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == reversed_ids


def test_reordenar_con_ids_invalidos(client, admin_headers, property_with_images) -> None:
    code = property_with_images.code
    image = upload(
        client, code, [("files", ("a.jpg", jpeg_bytes(), "image/jpeg"))], admin_headers
    ).json()[0]
    response = client.post(
        f"/api/admin/properties/{code}/images/reorder",
        json={"ids": [image["id"], 999999]},
        headers=admin_headers,
    )
    assert response.status_code in (400, 422)


def test_eliminar_imagen_borra_el_archivo(
    client, admin_headers, property_with_images
) -> None:
    code = property_with_images.code
    image = upload(
        client, code, [("files", ("a.jpg", jpeg_bytes(), "image/jpeg"))], admin_headers
    ).json()[0]

    static_root = get_settings().upload_path.parent
    file_path = static_root / image["url"].replace("/static/", "", 1)
    assert file_path.is_file()

    response = client.delete(
        f"/api/admin/properties/{code}/images/{image['id']}", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json() == []
    assert not file_path.exists()


def test_eliminar_imagen_principal_promueve_a_otra(
    client, admin_headers, property_with_images
) -> None:
    code = property_with_images.code
    images = upload(
        client,
        code,
        [
            ("files", ("a.jpg", jpeg_bytes(), "image/jpeg")),
            ("files", ("b.jpg", jpeg_bytes(), "image/jpeg")),
        ],
        admin_headers,
    ).json()
    main = next(item for item in images if item["is_main"])
    rest = next(item for item in images if not item["is_main"])

    updated = client.delete(
        f"/api/admin/properties/{code}/images/{main['id']}", headers=admin_headers
    ).json()
    assert len(updated) == 1
    assert updated[0]["id"] == rest["id"]
    assert updated[0]["is_main"] is True


def test_imagen_inexistente_devuelve_404(
    client, admin_headers, property_with_images
) -> None:
    response = client.delete(
        f"/api/admin/properties/{property_with_images.code}/images/999999",
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_subida_requiere_autenticacion(client, property_with_images) -> None:
    response = client.post(
        f"/api/admin/properties/{property_with_images.code}/images",
        files=[("files", ("a.jpg", jpeg_bytes(), "image/jpeg"))],
    )
    assert response.status_code == 401


def test_limites_de_subida(client, admin_headers) -> None:
    body = client.get("/api/admin/uploads-limit", headers=admin_headers).json()
    assert body["max_upload_mb"] >= 1
    assert "image/jpeg" in body["allowed_types"]
    assert body["max_images_per_property"] >= 1


def test_eliminar_propiedad_borra_sus_archivos(
    client, admin_headers, property_with_images
) -> None:
    code = property_with_images.code
    image = upload(
        client, code, [("files", ("a.jpg", jpeg_bytes(), "image/jpeg"))], admin_headers
    ).json()[0]
    static_root = get_settings().upload_path.parent
    file_path = static_root / image["url"].replace("/static/", "", 1)
    assert file_path.is_file()

    response = client.delete(f"/api/admin/properties/{code}", headers=admin_headers)
    assert response.status_code == 204
    assert not file_path.exists()
