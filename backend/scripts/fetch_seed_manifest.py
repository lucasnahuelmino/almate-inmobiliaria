"""Genera `backend/app/seed_images.json` con las fotografías de la demo.

Estrategia:
1. Primero consulta la API pública de **Openverse** (imágenes con licencias
   abiertas aptas para uso comercial: CC0, PDM, CC BY, CC BY-SA).
2. Si la API limita las consultas (403/429), recurre a **Wikimedia Commons**
   con una consulta alternativa por categoría.
3. Guarda el resultado incrementalmente, de modo que un reintento posterior
   sólo completa las categorías faltantes.

Uso:
    python scripts/fetch_seed_manifest.py

El archivo generado es el que usa `python -m app.cli seed` para descargar
las fotografías a `backend/app/static/seed/` (una sola vez).
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
OUTPUT = BACKEND_DIR / "app" / "seed_images.json"

USER_AGENT = "ALMATE-Propiedades-Demo/1.0 (datos de demostracion de ALMATE Digital Studio)"

PREFERRED = {"cc0", "pdm"}
ALLOWED = {"cc0", "pdm", "by", "by-sa"}

PER_CATEGORY = 3
MIN_WIDTH = 900
BETWEEN_REQUESTS = 25  # segundos: respeta el límite de consultas de Openverse

# Categoría → (consulta Openverse, consulta alternativa en Wikimedia Commons)
CATEGORIES: dict[str, tuple[str, str]] = {
    "living": (
        "modern living room interior design",
        'filetype:bitmap intitle:"living room" -painting -drawing -map',
    ),
    "kitchen": (
        "modern kitchen interior design",
        "filetype:bitmap intitle:kitchen intitle:modern -drawing",
    ),
    "bedroom": (
        "bedroom interior design",
        "filetype:bitmap intitle:bedroom intitle:interior -drawing",
    ),
    "bathroom": (
        "modern bathroom interior",
        "filetype:bitmap intitle:bathroom intitle:interior",
    ),
    "house": (
        "house exterior facade residential",
        'incategory:"Quality images of houses" filetype:bitmap',
    ),
    "garden": (
        "backyard garden house",
        "filetype:bitmap intitle:garden intitle:house",
    ),
    "building": (
        "apartment building facade exterior",
        "filetype:bitmap intitle:apartment intitle:building",
    ),
    "land": (
        "vacant land field plot",
        "filetype:bitmap intitle:field intitle:meadow",
    ),
    "storefront": (
        "commercial storefront shop street",
        "filetype:bitmap intitle:storefront",
    ),
    "office": (
        "office interior workspace",
        "filetype:bitmap intitle:office intitle:interior",
    ),
    "garage": (
        "garage interior parking",
        "filetype:bitmap intitle:garage intitle:interior",
    ),
    "detail": (
        "staircase architecture interior",
        "filetype:bitmap intitle:staircase intitle:interior",
    ),
}


def http_json(url: str, headers: dict[str, str], attempts: int = 3) -> dict | None:
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429, 503) and attempt < attempts - 1:
                wait = 60 * (attempt + 1)
                print(f"    límite de la API ({exc.code}); esperando {wait}s…", flush=True)
                time.sleep(wait)
                continue
            return None
        except Exception as exc:  # noqa: BLE001 - reintento simple de red
            if attempt < attempts - 1:
                time.sleep(10)
                continue
            print(f"    error de red: {exc}", flush=True)
            return None
    return None


def openverse(query: str) -> list[dict]:
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": query, "license_type": "commercial", "page_size": "20"}
    )
    payload = http_json(url, {"User-Agent": USER_AGENT}, attempts=3)
    results: list[dict] = []
    for item in (payload or {}).get("results", []):
        license_code = (item.get("license") or "").lower()
        if license_code not in ALLOWED:
            continue
        media_url = item.get("url") or ""
        if not media_url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")):
            continue
        width = item.get("width") or 0
        if width and width < MIN_WIDTH:
            continue
        results.append(
            {
                "url": media_url,
                "title": (item.get("title") or "").strip()[:140],
                "creator": (item.get("creator") or "").strip()[:120],
                "license": license_code.upper(),
                "license_version": item.get("license_version") or "",
                "license_url": item.get("license_url") or "",
                "source": item.get("foreign_landing_url") or "",
                "provider": (item.get("provider") or "openverse")[:40],
            }
        )
    results.sort(key=lambda item: 0 if item["license"] in PREFERRED else 1)
    return results


def commons(query: str) -> list[dict]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "12",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": "1600",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    payload = http_json(url, {"User-Agent": USER_AGENT}, attempts=2)
    results: list[dict] = []
    import re

    for page in list((payload or {}).get("query", {}).get("pages", {}).values()):
        title = page.get("title", "")
        if not re.search(r"\.(jpe?g|png)$", title, re.IGNORECASE):
            continue
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})

        def clean(value: str) -> str:
            return re.sub(r"<[^>]+>", "", value or "").strip()

        license_name = clean(meta.get("LicenseShortName", {}).get("value", ""))
        thumb = info.get("thumburl")
        if not thumb or (info.get("width") or 0) < MIN_WIDTH:
            continue
        results.append(
            {
                "url": thumb.split("?")[0],
                "title": title.replace("File:", ""),
                "creator": clean(meta.get("Artist", {}).get("value", ""))[:120],
                "license": license_name.upper()[:40],
                "license_version": "",
                "license_url": clean(meta.get("LicenseUrl", {}).get("value", "")),
                "source": title.replace("File:", "https://commons.wikimedia.org/wiki/File:"),
                "provider": "Wikimedia Commons",
            }
        )
        if len(results) >= PER_CATEGORY:
            break
    return results


def load_existing() -> list[dict]:
    if OUTPUT.exists():
        try:
            return json.loads(OUTPUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def save(manifest: list[dict]) -> None:
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    manifest = load_existing()
    for key, (ov_query, wm_query) in CATEGORIES.items():
        existing = [item for item in manifest if item.get("key", "").startswith(f"{key}-")]
        if len(existing) >= PER_CATEGORY:
            print(f"{key}: ya cargada ({len(existing)})", flush=True)
            continue

        print(f"{key}: consultando Openverse…", flush=True)
        found = openverse(ov_query)[:PER_CATEGORY]
        origin = "Openverse"
        if len(found) < PER_CATEGORY:
            time.sleep(BETWEEN_REQUESTS)
            print(f"{key}: consultando Wikimedia Commons…", flush=True)
            extra = commons(wm_query)
            known = {item["url"] for item in found}
            found += [item for item in extra if item["url"] not in known][
                : PER_CATEGORY - len(found)
            ]
            origin = "Openverse + Commons"

        manifest = [item for item in manifest if not item.get("key", "").startswith(f"{key}-")]
        for index, item in enumerate(found, start=1):
            manifest.append({"key": f"{key}-{index}", "query": ov_query, **item})

        save(manifest)
        print(f"{key}: {len(found)} imagen(es) [{origin}]", flush=True)
        time.sleep(BETWEEN_REQUESTS)

    print(f"\nTotal: {len(manifest)} imagenes -> {OUTPUT}", flush=True)
    return 0 if len(manifest) >= PER_CATEGORY * len(CATEGORIES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
