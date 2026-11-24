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
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
BRONCE = RAIZ / "data" / "bronce"
MANIFIESTO = BRONCE / "manifiesto.csv"
HUELLAS = BRONCE / "huellas_http.csv"  # ETag y tamaño del último archivo descargado por URL (E3)

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


# --------------------------------------------------------------------------- huella HTTP (E3)
# Optimización de la captura: antes de bajar un ZIP de decenas de MB se pide solo
# su primer byte (petición parcial, "Range: bytes=0-0"). El INEGI contesta con el
# ETag, la fecha de modificación y el tamaño total del archivo.
#
# El INEGI tiene varios servidores con copias del mismo archivo: cada copia tiene
# su propio ETag y una fecha de modificación que difiere por segundos (medido el
# 2026-11-24). Por eso el archivo se considera SIN CAMBIOS si:
#     mismo tamaño en bytes  Y  (ETag ya visto para esa URL  O  fecha a <= 10 min)
# Cada ETag nuevo con el mismo contenido (mismo SHA-256 tras descargar) se agrega
# a la lista, así el sistema "aprende" las copias de cada servidor.
# Si el servidor no da esos datos (o responde HTML), se descarga como antes:
# ante la duda, siempre se baja el archivo.
CAMPOS_HUELLA = ["url", "etags", "last_modified", "bytes", "fecha_verificacion_utc"]
TOLERANCIA_FECHA_SEG = 600


def huella_remota(url: str) -> dict | None:
    try:
        with requests.get(url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"},
                          stream=True, timeout=60) as r:
            rango = r.headers.get("Content-Range", "")
            if r.status_code != 206 or "html" in r.headers.get("Content-Type", "") or "/" not in rango:
                return None
            return {"etag": r.headers.get("ETag", "").strip('"'), "last_modified": r.headers.get("Last-Modified", ""),
                    "bytes": rango.rsplit("/", 1)[1]}
    except requests.RequestException:
        return None


def leer_huellas() -> dict[str, dict]:
    if not HUELLAS.exists():
        return {}
    with open(HUELLAS, newline="", encoding="utf-8") as f:
        return {r["url"]: r for r in csv.DictReader(f)}


def _fecha_http(txt: str) -> datetime | None:
    try:
        return parsedate_to_datetime(txt)
    except (TypeError, ValueError):
        return None


def sin_cambios(url: str) -> tuple[bool, dict | None]:
    """(True si el archivo remoto es el mismo que la última vez, huella remota)."""
    remota = huella_remota(url)
    local = leer_huellas().get(url)
    if not remota or not local or remota["bytes"] != local["bytes"]:
        return False, remota
    if remota["etag"] and remota["etag"] in local["etags"].split("|"):
        return True, remota
    f_r, f_l = _fecha_http(remota["last_modified"]), _fecha_http(local["last_modified"])
    cerca = bool(f_r and f_l and abs((f_r - f_l).total_seconds()) <= TOLERANCIA_FECHA_SEG)
    return cerca, remota


def guardar_huella(url: str, huella: dict | None) -> None:
    """Se llama solo después de confirmar el contenido (descarga + SHA-256)."""
    if not huella:
        return
    todas = leer_huellas()
    previa = todas.get(url)
    etags = set(previa["etags"].split("|")) if previa and previa["bytes"] == huella["bytes"] else set()
    etags.discard("")
    etags.add(huella["etag"])
    todas[url] = {"url": url, "etags": "|".join(sorted(etags)), "last_modified": huella["last_modified"],
                  "bytes": huella["bytes"], "fecha_verificacion_utc": ahora_utc()}
    with open(HUELLAS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_HUELLA, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(todas.values(), key=lambda r: r["url"]))


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
