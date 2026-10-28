# PLAN.md — ALMATE Propiedades

**Proyecto:** ALMATE Propiedades · **Marca madre:** ALMATE Digital Studio
**Fecha de inicio:** 2026-10-25 · **Estado:** en desarrollo

---

## 0. Diagnóstico inicial (Fase 0)

| Aspecto | Resultado de la inspección |
|---|---|
| Contenido del directorio | Vacío (sin archivos ni carpetas) |
| Repositorio Git | No existía → inicializado en esta fase |
| Python | 3.13.9 disponible, `pip` 25.2 |
| Node / npm | v24.19.0 / 11.17.0 |
| Git | 2.51.1.windows.1 |
| Red | Acceso a PyPI y registry npm verificado (instalación de dependencias comprobada) |
| Stack previo | Ninguno → se aplica la stack sugerida en las instrucciones |

**Conclusión:** proyecto vacío. Se crea una estructura limpia y profesional con la stack
solicitada (Vue 3 + TypeScript + Vite + Vue Router + Pinia / FastAPI + SQLAlchemy 2 + Alembic +
Pydantic / SQLite con preparación para PostgreSQL).

---

## 1. Decisiones técnicas

| # | Decisión | Justificación |
|---|---|---|
| D1 | Monorepo con `backend/` y `frontend/` en un único repositorio | Demo autocontenida, comandos simples en Windows. |
| D2 | **Importes en centavos** (`price_cents BIGINT`) en lugar de `FLOAT` | Evita errores monetarios por punto flotante; permite ordenar y filtrar numéricamente en SQLite y PostgreSQL. Se exponen en la API como decimales. |
| D3 | Dos estados independientes por propiedad: **comercial** (`available / reserved / sold / rented`) y **publicación** (`draft / published / archived`) | Los conceptos son distintos y el público solo debe ver `published`. |
| D4 | Autenticación por **JWT (HS256)** + contraseña con **bcrypt** | Validación real en backend, sin secretos en el repositorio. |
| D5 | Código de referencia legible (`ALM-XXXX-YY`) + UUID interno | Identificador estable para URLs públicas y soporte. |
| D6 | Fotos en `backend/app/static/uploads/` con nombre UUID, validadas por *magic bytes* + Pillow | Sin rutas arbitrarias ni nombres inseguros; preparado para migrar a S3/Cloudinary. |
| D7 | Imágenes de demo descargadas de **Wikimedia Commons** (licencias CC0/PD/CC-BY) al directorio `static/seed/` | Fotografías reales, con licencia documentada, reemplazables y locales (no se rompen sin internet). |
| D8 | Proxy de Vite `/api` y `/static` → `127.0.0.1:8000` | El navegador ve un único origen en desarrollo; evita CORS innecesario. |
| D9 | `Emprendimientos` = propiedad con `is_development = true` | Permite una sección editorial sin inventar una entidad nueva. |
| D10 | Favoritos en `localStorage` con aviso explícito en la UI | Correcto para una demo sin cuentas de usuario públicas. |
| D11 | WhatsApp: solo se **abre** `wa.me` con mensaje precompuesto; número configurable en Ajustes | No se afirma envío automático. |
| D12 | Panel `/admin` con `noindex` y guardas de ruta + autorización en backend | La seguridad real vive en el servidor. |

---

## 2. Arquitectura

```
Inmobiliaria/
├── PLAN.md  TASKS.md  README.md  .env.example  .gitignore
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
+   ├── alembic/                      # migraciones
│   ├── app/
│   │   ├── main.py                   # app FastAPI, CORS, static, routers
│   │   ├── config.py                 # pydantic-settings (.env)
│   │   ├── database.py               # engine, Session, Base
│   │   ├── models/                   # SQLAlchemy 2 (users, properties, images,
│   │   │                             #  inquiries, valuation, listing, settings, notes)
│   │   ├── schemas/                  # Pydantic v2 (contratos de la API)
│   │   ├── api/                      # routers públicos y privados + deps/auth
│   │   ├── services/                 # lógica: filtros, imágenes, métricas, seed
│   │   ├── static/uploads/           # fotografías subidas
│   │   ├── static/seed/              # fotografías de demo descargadas
│   │   └── cli.py                    # create-admin / seed / reset
│   └── tests/                        # Pytest
├── frontend/
│   ├── package.json  vite.config.ts  tsconfig.json  index.html
│   └── src/
│       ├── main.ts  App.vue
│       ├── router/  stores/  api/     # cliente HTTP tipado
│       ├── styles/                   # tokens, base, utilidades
│       ├── components/               # público (cards, filtros…) y admin
│       └── pages/                    # público y /admin
└── scripts/                          # atajos de Windows (.ps1)
```

**Puertos:** backend `8000`, frontend `5173` (configurables por `.env`).

---

## 3. Modelo de datos (resumen)

- `users` — id, email único, password_hash (bcrypt), nombre, rol (`admin`/`editor`), activo, timestamps.
- `properties` — id (UUID), código único, título, descripción, operación, tipo, categoría,
  `price_cents`, moneda, `expenses_cents`, estado comercial, estado publicación, destacada,
  `is_development`, dirección + `address_is_public`, país/provincia/partido/localidad/barrio,
  ambientes/dormitorios/baños/toilettes/cocheras/antigüedad, superficies (cubierta, semicubierta,
  total), servicios (JSON), apto_profesional, fechas (creación/actualización/publicación),
  `published_at`, `created_by`.
- `property_images` — id, property_id (FK, cascade), filename, url, alt, `is_main`, `sort_order`,
  tamaño, tipo MIME, timestamps.
- `inquiries` — consulta por propiedad o general: nombre, email, teléfono, mensaje,
  property_id (nullable), estado (`new/following/answered/closed`), `internal_notes`.
- `valuation_requests` — tasación: datos de contacto + datos del inmueble + estado.
- `listing_requests` — oferta de propiedad: datos de contacto + inmueble + estado.
- `business_settings` — singleton (clave/valor tipado): marca, logo, teléfonos, WhatsApp, email,
  dirección, redes, textos, moneda, crédito ALMATE.
- `internal_note` — notas administrativas polimórficas (`target_type`, `target_id`).

**Índices:** properties(publication_status, commercial_status, operation, type, locality,
price_cents, is_development, published_at), property_images(property_id, sort_order),
inquiries(status, created_at), etc.

---

## 4. Fases

| Fase | Contenido | Estado |
|---|---|---|
| 0 | Inspección, diagnóstico y plan | ✅ |
| 1 | Estructura, documentación (`PLAN.md`, `TASKS.md`, `README.md`), modelo de datos y migraciones | ✅ |
| 2 | Backend: API, autenticación, seguridad, CLI (admin + seed) | ✅ |
| 3 | Sitio público: home, catálogo, filtros, ficha, formularios | ✅ |
| 4 | Panel: login, CRUD de propiedades, gestión de fotos | ✅ |
| 5 | Consultas, solicitudes, configuración y dashboard | ✅ |
| 6 | Responsive, accesibilidad y SEO | ✅ |
| 7 | Pruebas integrales (Pytest + Vitest), correcciones, documentación final | ✅ |
| 8 | Preparación para demo y despliegue futuro | ✅ |

---

## 5. Verificaciones por fase

Cada fase se da por terminada solo cuando:

1. Los comandos de la fase se ejecutan sin errores.
2. Las pruebas asociadas pasan (`pytest`, `npm run test:unit`, `vue-tsc`).
3. `TASKS.md` queda actualizado con la evidencia.
4. Se crea un checkpoint de Git.

---

## 6. Pendientes documentados (ver `README.md` §Pendientes)

- HTTPS, copias de backups, monitoreo y política de privacidad antes de uso productivo.
- Almacenamiento externo de imágenes (S3/Cloudinary) y CDN.
- SSR/prerenderizado para SEO avanzado.
- Multiempresa (schema por inmobiliaria) sólo si se necesita.
