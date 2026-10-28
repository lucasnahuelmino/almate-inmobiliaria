"""Autenticación, roles y permisos del panel administrativo."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import ADMIN_EMAIL, EDITOR_EMAIL, PASSWORD


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_login_correcto(client: TestClient) -> None:
    response = _login(client, ADMIN_EMAIL, PASSWORD)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["expires_in"] > 0
    assert body["user"]["email"] == ADMIN_EMAIL
    assert body["user"]["role"] == "admin"
    # Nunca se devuelve el hash de la contraseña.
    assert "password" not in response.text


def test_login_con_contraseña_incorrecta(client: TestClient) -> None:
    response = _login(client, ADMIN_EMAIL, "ContraseñaQueNoEs")
    assert response.status_code == 401
    assert response.json()["message"]


def test_login_sin_usuario_no_revela_que_no_existe(client: TestClient) -> None:
    response = _login(client, "nadie@inexistente.com", PASSWORD)
    assert response.status_code == 401
    # Mismo mensaje que una contraseña incorrecta (sin enumerar cuentas).
    assert response.json()["message"] == "Credenciales inválidas."


def test_login_con_email_invalido(client: TestClient) -> None:
    response = _login(client, "no-es-correo", PASSWORD)
    assert response.status_code == 422


def test_me_con_token_valido(client: TestClient, admin_headers) -> None:
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == ADMIN_EMAIL


def test_me_sin_token(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_token_falsificado(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer token-inventado"}
    )
    assert response.status_code == 401


def test_token_con_formato_invalido(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer"})
    assert response.status_code in (401, 403)


def test_editor_puede_usar_el_panel(client: TestClient, editor_headers) -> None:
    response = client.get("/api/admin/dashboard", headers=editor_headers)
    assert response.status_code == 200
    assert response.json()["counts"]["properties_total"] >= 0


def test_editor_no_puede_borrar_propiedades(
    client: TestClient, editor_headers
) -> None:
    response = client.delete("/api/admin/properties/ALM-CAT-99", headers=editor_headers)
    assert response.status_code == 403
    assert response.json()["message"]


def test_editor_no_puede_cambiar_la_configuracion(
    client: TestClient, editor_headers
) -> None:
    response = client.put(
        "/api/admin/settings", json={"phone": "+54 11 0000-0000"}, headers=editor_headers
    )
    assert response.status_code == 403


def test_admin_si_puede_leer_la_configuracion(client: TestClient, admin_headers) -> None:
    response = client.get("/api/admin/settings", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["brand_name"]


def test_limite_de_intentos_de_login(client: TestClient) -> None:
    """A partir del noveno intento en un minuto responde 429."""
    statuses = [
        _login(client, ADMIN_EMAIL, f"clave-erronea-{index}").status_code
        for index in range(9)
    ]
    assert statuses[-1] == 429
    assert all(status == 401 for status in statuses[:-1])
    # Sigue bloqueado para el resto de la ventana.
    assert _login(client, ADMIN_EMAIL, PASSWORD).status_code == 429
