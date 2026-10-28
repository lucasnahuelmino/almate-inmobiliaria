"""Configuración de la aplicación ALMATE Propiedades.

Los valores se leen de variables de entorno y, opcionalmente, de un archivo
`.env` (raíz del proyecto o carpeta `backend/`). Nunca se hardcodean secretos.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent          # backend/app
BACKEND_DIR = BASE_DIR.parent                       # backend/
ROOT_DIR = BACKEND_DIR.parent                       # raíz del proyecto

ENV_FILES = (ROOT_DIR / ".env", BACKEND_DIR / ".env")


class Settings(BaseSettings):
    """Ajustes globales accesibles vía `app.config.get_settings()`."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Identidad / entorno -------------------------------------------
    app_name: str = "ALMATE Propiedades"
    app_env: str = Field(default="development")
    app_debug: bool = False

    # --- Servidor -------------------------------------------------------
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    # --- Base de datos --------------------------------------------------
    database_url: str = "sqlite:///./almate.db"

    # --- Seguridad ------------------------------------------------------
    secret_key: str = "dev-insecure-secret-key-change-me-before-production"
    access_token_expire_minutes: int = 720
    algorithm: str = "HS256"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Multimedia -----------------------------------------------------
    max_upload_mb: int = 8
    max_images_per_property: int = 30
    upload_dir: str = "app/static/uploads"
    allowed_image_types: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        return path

    @property
    def seed_images_path(self) -> Path:
        return BASE_DIR / "static" / "seed"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @field_validator("app_env")
    @classmethod
    def _normalise_env(cls, value: str) -> str:
        return value.strip().lower()

    def warn_if_insecure(self, logger: logging.Logger) -> None:
        """Avisa (sin bloquear) cuando la configuración no es de producción."""
        if self.secret_key.startswith("dev-insecure"):
            if self.is_production:
                raise RuntimeError(
                    "SECRET_KEY no fue configurada. Genere una con "
                    "`python -c \"import secrets; print(secrets.token_urlsafe(64))\"` "
                    "y defínala en el archivo .env antes de usar producción."
                )
            logger.warning(
                "Usando SECRET_KEY de desarrollo. Genere una propia antes de producción."
            )
        if self.is_production and "*" in self.cors_origins:
            raise RuntimeError("CORS no puede ser abierto ('*') en producción.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton de configuración (cacheado por proceso)."""
    return Settings()
