# TASKS.md — ALMATE Propiedades

Tareas verificables. Una tarea se marca `[x]` **solo después de comprobarla**.
La columna "Evidencia" registra el comando ejecutado y su resultado.

Leyenda: `⬜` pendiente · `🔶` en progreso · `✅` verificada

---

## Fase 0 — Inspección, diagnóstico y plan

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 0.1 | Inspeccionar directorio y detectar stack existente | ✅ | Directorio vacío; Python 3.13.9, Node 24, npm 11, Git 2.51 |
| 0.2 | Verificar acceso a PyPI y npm | ✅ | `pip install fastapi…` → ok 0.162.0; `npm ping` → PONG |
| 0.3 | Inicializar Git | ✅ | `git init` → repositorio creado |
| 0.4 | Crear `PLAN.md` con fases y decisiones | ✅ | Archivo presente |

## Fase 1 — Estructura, documentación y modelo de datos

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 1.1 | `.gitignore` y `.env.example` sin secretos | ✅ | Archivos creados (`.env` y `*.db` ignorados) |
| 1.2 | Estructura `backend/` y `frontend/` | ✅ | Árbol de carpetas creado |
| 1.3 | Modelos SQLAlchemy 2 con relaciones, índices e integridad | ✅ | 8 modelos + enums controlados (`app/models/`) |
| 1.4 | Alembic configurado + migración inicial | ✅ | `alembic upgrade head` → 9 tablas creadas |
| 1.5 | `README.md` con instalación y ejecución | ⬜ | Pendiente (se escribe en Fase 7) |

## Fase 2 — Backend, base de datos, migraciones y autenticación

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 2.1 | App FastAPI con routers, CORS y static | ✅ | `python scripts/smoke.py` → `/api/health` 200 |
| 2.2 | Endpoints públicos de propiedades (lista, detalle, filtros) | ✅ | `GET /api/properties?operation=buy&type=house` → 200 y filtrado correcto |
| 2.3 | Formularios públicos persisten en BD | ✅ | `POST /api/inquiries` → 201 con `id`; registro en tabla |
| 2.4 | Login con bcrypt + JWT + guardas de autorización | ✅ | login ok → token; `/api/admin/*` sin token → 401; editor → 403 en borrado |
| 2.5 | CLI: crear administrador | ✅ | `python -m app.cli create-admin` → usuario creado con hash bcrypt |
| 2.6 | CLI: seed idempotente de datos de demo | ✅ | `python -m app.cli seed` ×2 → 21 propiedades nuevas la 1ª, 0 la 2ª |
| 2.7 | Manejo de errores y validaciones de servidor | ✅ | Payload inválido → 422 con `{message, errors[]}` |
| 2.8 | Límite de tasa (login/formularios) | ✅ | `pytest tests/test_auth.py::test_limite_de_intentos_de_login` → 429 |

## Fase 3 — Sitio público

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 3.1 | Home: header, hero, buscador, destacadas, recientes, servicios, CTA, contacto, footer | ⬜ | |
| 3.2 | Catálogos Comprar / Alquilar / Alquiler temporal / Emprendimientos | ⬜ | |
| 3.3 | Filtros combinables + orden + paginación + limpiar + contador + vacío | ⬜ | |
| 3.4 | Filtros y paginación conservados en la URL | ⬜ | |
| 3.5 | Tarjeta inmobiliaria completa con estados y favorito local | ⬜ | |
| 3.6 | Ficha de propiedad con galería, características, contacto, WhatsApp y similares | ⬜ | |
| 3.7 | Formularios público: contacto, tasación, publicación (front + back) | ⬜ | |
| 3.8 | Páginas Nosotros / Contacto / 404 | ⬜ | |

## Fase 4 — Panel administrativo

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 4.1 | Login, sesión, logout, guardas de ruta | ⬜ | |
| 4.2 | CRUD de propiedades con formulario por secciones | ⬜ | |
| 4.3 | Cambios de estado (publicar/despublicar/reservar/vender/alquilar/archivar/eliminar) | ⬜ | |
| 4.4 | Subida de fotos con previsualización, principal, orden, alt y borrado | ⬜ | |
| 4.5 | Buscador y filtros administrativos + paginación | ⬜ | |

## Fase 5 — Consultas, solicitudes, configuración y dashboard

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 5.1 | Bandeja de consultas con estados y notas internas | ⬜ | |
| 5.2 | Solicitudes de tasación y de publicación | ⬜ | |
| 5.3 | Configuración del negocio persistente | ⬜ | |
| 5.4 | Dashboard con métricas reales calculadas | ⬜ | |

## Fase 6 — Diseño, accesibilidad y SEO

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 6.1 | Sistema de diseño (tokens, tipografía serif/sans, paleta) | ⬜ | |
| 6.2 | Responsive desktop/tablet/móvil (público y panel) | ⬜ | |
| 6.3 | Accesibilidad: foco, contraste, etiquetas, `alt`, navegación por teclado | ⬜ | |
| 6.4 | SEO: títulos por ruta, meta description, Open Graph, canonical, robots.txt, sitemap | ⬜ | |
| 6.5 | `/admin` marcado `noindex` | ⬜ | |

## Fase 7 — Pruebas y documentación final

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 7.1 | Pytest: cobertura de los 20 puntos obligatorios (backend) | ✅ | `python -m pytest` → **134 passed** |
| 7.2 | Vitest: pruebas de lógica/componentes del frontend | ⬜ | |
| 7.3 | Type-check del frontend (`vue-tsc`) | ⬜ | |
| 7.4 | Sin errores críticos en consola del navegador | ⬜ | |
| 7.5 | README final con comandos, puertos, troubleshooting y pendientes | ⬜ | |

## Fase 8 — Demo y despliegue futuro

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| 8.1 | Build de producción verificado (`npm run build`) | ⬜ | |
| 8.2 | Documento de personalización para otras inmobiliarias | ⬜ | |
| 8.3 | Documento de pendientes para producción | ⬜ | |
| 8.4 | Checkpoints de Git por fase | 🔶 | Commit inicial del backend pendiente |

---

## Incidencias detectadas y corregidas

| Fase | Incidencia | Corrección |
|---|---|---|
| 2 | `HTTPBearer(scheme=)` no existe en FastAPI actual | Parámetro `scheme_name` |
| 2 | `back_populates="property"` pisaba el builtin | Renombrado a `property_ref` |
| 2 | `validation_detail` recibía lista o `ValidationError` | Acepta ambos tipos |
| 2 | Falta `email-validator` y `Pillow` en el entorno | Agregados a `requirements.txt` |
| 2 | Falta el directorio `app/static/` (rompía el arranque) | Creado con `.gitkeep` |
| 2 | `to_admin()` pasaba `created_at` dos veces | Se reutiliza `to_detail()` |
| 2 | `to_admin()` pasaba `images` dos veces | Se descarta el `images` de `to_detail()` |
| 2 | Emails `.local` rechazados por validación Pydantic | Correos de prueba en `.com` |
