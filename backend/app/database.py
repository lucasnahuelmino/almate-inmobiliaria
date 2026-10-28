"""Conexión a la base de datos (SQLAlchemy 2.x).

`DATABASE_URL` permite cambiar de SQLite a PostgreSQL sin tocar el código:
sólo se modifica la variable de entorno.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    # SQLite necesita `check_same_thread=False` para usarse desde FastAPI.
    connect_args = {"check_same_thread": False}

engine: Engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos."""


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # pragma: no cover
    """FK activas + WAL en SQLite (no aplica a otros dialectos)."""
    if dbapi_connection.__class__.__name__ == "Connection":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: sesión de base de datos por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """Crea las tablas si no existen (útil para la primera ejecución y tests)."""
    from app import models  # noqa: F401  (registro de modelos)

    Base.metadata.create_all(bind=engine)
