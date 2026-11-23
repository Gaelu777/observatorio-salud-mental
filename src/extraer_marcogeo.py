"""Extractor Bronce: Marco Geoestadístico 2020 (INEGI) — Colima, capa municipal.

Polígonos oficiales de los 10 municipios (misma vintage que el Censo 2020, así
las claves coinciden). El zip del estado pesa ~29 MB porque trae manzanas,
AGEB, localidades, etc.; solo se guardan los archivos del shapefile municipal
(`06mun.*`, ~300 KB) byte por byte.

Es un producto fijo: si ya está en el manifiesto y en disco, NO se vuelve a
descargar (no tiene sentido bajar 29 MB cada mes para obtener lo mismo).
"""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from comun import BRONCE, RAIZ, ahora_utc, descargar, registrar, sha256, ultimo_hash

URL = ("https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/"
       "productos/geografia/marcogeo/889463807469/06_colima.zip")
SALIDA = BRONCE / "inegi_marcogeo2020"
CAPA = "06mun"


def main() -> None:
    shp = SALIDA / f"{CAPA}.shp"
    if ultimo_hash(URL) and shp.exists():
        print("Marco Geoestadístico 2020: ya ingerido (producto fijo), se omite")
        return
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "mg_06.zip"
        descargar(URL, zip_path)
        h, tam = sha256(zip_path), zip_path.stat().st_size
        SALIDA.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            for n in z.namelist():
                if n.startswith(f"conjunto_de_datos/{CAPA}."):
                    (SALIDA / Path(n).name).write_bytes(z.read(n))
    registrar({
        "fuente": "INEGI-MARCOGEO2020",
        "url": URL,
        "fecha_ingesta_utc": ahora_utc(),
        "sha256_origen": h,
        "bytes_origen": tam,
        "archivo_bronce": shp.relative_to(RAIZ).as_posix(),
        "registros": 10,
    })
    print("Marco Geoestadístico 2020: capa municipal guardada")


if __name__ == "__main__":
    main()
