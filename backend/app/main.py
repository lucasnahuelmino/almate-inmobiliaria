"""Aplicación FastAPI de ALMATE Propiedades.

Monta la API (`/api`), los archivos estáticos (`/static`) y la documentación
interactiva (`/docs`). El frontend Vue se sirve por separado en desarrollo.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api import admin_images, admin_leads, admin_properties, admin_settings, auth, dashboard, forms, public
from app.api.errors import validation_detail
from app.config import get_settings
from app.database import init_database

logger = logging.getLogger("almate")
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Arranque: aviso de configuración y creación de tablas si faltan."""
    settings.warn_if_insecure(logger)
    init_database()
    logger.info("%s v%s iniciada (%s)", settings.app_name, __version__, settings.app_env)
    yield


app = FastAPI(
    title="API de ALMATE Propiedades",
    description=(
        "API REST de la demo inmobiliaria **ALMATE Propiedades** (ALMATE Digital Studio).\n\n"
        "Puntos de acceso *públicos*: catálogo, detalle y formularios.\n"
        "Puntos de acceso *privados* (`/api/admin/*`): requieren token Bearer obtenido en "
        "`POST /api/auth/login`.\n\n"
        "Los importes viajan como cadenas decimales (ej. `\"152000.50\"`) y se almacenan en "
        "centavos para evitar errores de punto flotante."
    ),
    version=__version__,
    lifespan=lifespan,
    contact={"name": "ALMATE Digital Studio", "url": "https://almatedigital.studio"},
    license_info={"name": "Demo comercial — uso de demostración"},
    openapi_url="/api/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS (sólo orígenes conocidos en desarrollo) ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Cabeceras de seguridad básicas y `noindex` para rutas administrativas."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith(("/admin", "/api/admin", "/docs")):
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow")
    return response


# --- Manejo de errores coherente -------------------------------------------
def _body(message: str, errors: list | dict | None = None) -> dict:
    return {"message": message, "errors": errors or []}


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_request: Request, exc: RequestValidationError):
    """422 con el mismo formato de error que el resto de la API."""
    return JSONResponse(
        status_code=422,
        content=_body("Los datos enviados no son válidos.", validation_detail(exc.errors())),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        content = detail if "message" in detail else _body(str(detail))
    else:
        content = _body(str(detail))
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    logger.warning("Valor inválido recibido: %s", exc)
    return JSONResponse(status_code=422, content=_body(str(exc)))


@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, exc: Exception):
    """No se filtra información interna al cliente."""
    logger.exception("Error no controlado: %s", exc)
    return JSONResponse(
        status_code=500,
        content=_body("Ocurrió un error inesperado. Intentá nuevamente en unos minutos."),
    )


# --- Rutas de la API --------------------------------------------------------
API_PREFIX = "/api"
app.include_router(public.router, prefix=API_PREFIX)
app.include_router(forms.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(admin_properties.router, prefix=API_PREFIX)
app.include_router(admin_images.router, prefix=API_PREFIX)
app.include_router(admin_leads.router, prefix=API_PREFIX)
app.include_router(admin_settings.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


@app.get("/api/version", tags=["Público"])
def version() -> dict:
    return {"name": settings.app_name, "version": __version__, "environment": settings.app_env}


# --- Archivos estáticos (fotografías) ---------------------------------------
# `/static/...` sirve `backend/app/static/`, que contiene `uploads/` y `seed/`.
app.mount("/static", StaticFiles(directory=settings.upload_path.parent), name="static")
