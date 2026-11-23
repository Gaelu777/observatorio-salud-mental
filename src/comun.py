"""Utilidades compartidas por los extractores de la capa Bronce.

Reglas éticas que aplican todos los extractores:
- Solo se descargan archivos públicos de rutas permitidas por robots.txt.
- User-Agent identificable (sin datos personales) y pausa entre descargas.
- Cada descarga queda registrada en data/bronce/manifiesto.csv (linaje):
  URL de origen, fecha de ingesta (UTC), hash SHA-256 del archivo original,
  archivo generado y número de registros.
"""
from __future__ import annotations

import csv
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
BRONCE = RAIZ / "data" / "bronce"
MANIFIESTO = BRONCE / "manifiesto.csv"

USER_AGENT = "observatorio-salud-mental-colima/0.1 (proyecto academico; datos abiertos INEGI)"
PAUSA_SEG = 5  # pausa de cortesía entre descargas para no saturar el servidor
CAMPOS_MANIFIESTO = [
    "fuente", "url", "fecha_ingesta_utc", "sha256_origen", "bytes_origen",
    "archivo_bronce", "registros",
]


def descargar(url: str, destino: Path, reintentos: int = 3) -> Path:
    """Descarga `url` a `destino` en streaming; falla si el servidor responde HTML.

    INEGI responde 200 + página HTML de "no encontrada" cuando la ruta no existe,
    por eso se valida el Content-Type además del código HTTP.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    for intento in range(1, reintentos + 1):
        try:
            with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=120) as r:
                r.raise_for_status()
                tipo = r.headers.get("Content-Type", "")
                if "html" in tipo:
                    raise ValueError(f"Respuesta HTML (archivo no disponible): {url}")
                with open(destino, "wb") as f:
                    for bloque in r.iter_content(chunk_size=1 << 20):
                        f.write(bloque)
            return destino
        except (requests.RequestException, ValueError) as e:
            if intento == reintentos or isinstance(e, ValueError):
                raise
            time.sleep(PAUSA_SEG * intento)
    raise RuntimeError("inalcanzable")


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def ahora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def leer_manifiesto() -> list[dict]:
    if not MANIFIESTO.exists():
        return []
    with open(MANIFIESTO, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ultimo_hash(url: str) -> str | None:
    """Hash del último archivo ingerido desde `url` (para no reingerir lo mismo)."""
    filas = [r for r in leer_manifiesto() if r["url"] == url]
    return filas[-1]["sha256_origen"] if filas else None


def registrar(fila: dict) -> None:
    """Agrega una fila al manifiesto (solo se agrega, nunca se reescribe)."""
    nuevo = not MANIFIESTO.exists()
    MANIFIESTO.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFIESTO, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_MANIFIESTO)
        if nuevo:
            w.writeheader()
        w.writerow(fila)
