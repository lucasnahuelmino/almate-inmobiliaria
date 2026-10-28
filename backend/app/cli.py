"""Herramientas de línea de comandos de ALMATE Propiedades.

Ejecutar desde la carpeta `backend/` con el entorno virtual activado:

    python -m app.cli init-db
    python -m app.cli create-admin --email admin@demo.com --name "Admin Demo"
    python -m app.cli seed
    python -m app.cli list-users

La contraseña se puede pasar con `--password` (útil para demostraciones
automatizadas) o escribirla de forma interactiva, que es el modo recomendado:
no queda registrada en el historial de la terminal.
"""

from __future__ import annotations

import argparse
import getpass
import logging
import sys

from sqlalchemy import select

from app.database import SessionLocal, init_database
from app.models.lead import Inquiry, ListingRequest, ValuationRequest
from app.models.property import Property, PropertyImage
from app.models.settings import BusinessSettings
from app.models.user import User, UserRole
from app.services.seed import ensure_demo_admin, run_seed

logger = logging.getLogger("almate.cli")


def _print(message: str) -> None:
    print(message, flush=True)


def cmd_init_db(_args: argparse.Namespace) -> int:
    init_database()
    _print("Base de datos inicializada (tablas creadas si no existían).")
    _print("Para esquema versionado usá:  python -m alembic upgrade head")
    return 0


def cmd_create_admin(args: argparse.Namespace) -> int:
    if args.role not in ("admin", "editor"):
        _print("El rol debe ser 'admin' o 'editor'.")
        return 2

    password = args.password
    if not password:
        password = getpass.getpass("Contraseña del usuario: ")
        confirmation = getpass.getpass("Repetí la contraseña: ")
        if password != confirmation:
            _print("Las contraseñas no coinciden.")
            return 1
    if len(password) < 8:
        _print("La contraseña debe tener al menos 8 caracteres.")
        return 1

    init_database()
    db = SessionLocal()
    try:
        email = args.email.strip().lower()
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, full_name=args.name.strip() or "Administrador")
            db.add(user)
        user.full_name = args.name.strip() or user.full_name
        user.role = UserRole(args.role)
        user.is_active = True

        from app.security import hash_password

        user.password_hash = hash_password(password)
        db.commit()
        _print(f"Usuario {user.email} creado/actualizado con rol '{user.role.value}'.")
        _print("La contraseña se guardó hasheada (bcrypt); no se almacena en claro.")
        return 0
    finally:
        db.close()


def cmd_seed(args: argparse.Namespace) -> int:
    init_database()
    db = SessionLocal()
    try:
        if args.admin_email:
            password = args.admin_password or "AlmateDemo2026!"
            ensure_demo_admin(db, args.admin_email, password, args.admin_name)
            _print(f"Administrador listo: {args.admin_email}")
            if not args.admin_password:
                _print("  (contraseña generada por defecto: AlmateDemo2026!)")

        result = run_seed(db)
        _print("Carga de demostración finalizada:")
        _print(f"  · propiedades nuevas ...... {result['propiedades_nuevas']}")
        _print(f"  · propiedades totales ..... {result['propiedades_total']}")
        _print(f"  · imágenes disponibles .... {result['imagenes_disponibles']}")
        _print(f"  · imágenes registradas .... {result['imagenes_registradas']}")
        _print(f"  · consultas/solicitudes ... {result['leads_nuevos']}")
        return 0
    finally:
        db.close()


def cmd_status(_args: argparse.Namespace) -> int:
    init_database()
    db = SessionLocal()
    try:
        props = len(db.scalars(select(Property)).all())
        images = len(db.scalars(select(PropertyImage)).all())
        inquiries = len(db.scalars(select(Inquiry)).all())
        valuations = len(db.scalars(select(ValuationRequest)).all())
        listings = len(db.scalars(select(ListingRequest)).all())
        users = len(db.scalars(select(User)).all())
        BusinessSettings.get_or_create(db)
        _print("Estado de la base de datos")
        _print(f"  propiedades ............. {props}")
        _print(f"  fotografías ............. {images}")
        _print(f"  consultas ............... {inquiries}")
        _print(f"  tasaciones .............. {valuations}")
        _print(f"  publicaciones ofrecidas . {listings}")
        _print(f"  usuarios administrativos  {users}")
        return 0
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli", description="CLI de ALMATE Propiedades")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Crea las tablas de la base de datos").set_defaults(
        func=cmd_init_db
    )

    admin = sub.add_parser("create-admin", help="Crea o actualiza un usuario administrativo")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", default="Administrador")
    admin.add_argument("--password", default=None, help="Si se omite, se pide de forma interactiva")
    admin.add_argument("--role", default="admin", choices=["admin", "editor"])
    admin.set_defaults(func=cmd_create_admin)

    seed = sub.add_parser("seed", help="Carga datos de demostración (idempotente)")
    seed.add_argument("--admin-email", default=None, help="Crea también este administrador")
    seed.add_argument("--admin-password", default=None)
    seed.add_argument("--admin-name", default="Administrador Demo")
    seed.set_defaults(func=cmd_seed)

    sub.add_parser("status", help="Muestra el conteo de registros").set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
