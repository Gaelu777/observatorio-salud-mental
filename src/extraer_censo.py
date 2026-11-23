"""Extractor Bronce: Censo de Población y Vivienda 2020, INEGI — ITER Colima.

Principales resultados por localidad (ITER) del estado de Colima. Se usa como
denominador de población para calcular tasas por 100 mil habitantes.

Es un archivo pequeño (~150 KB) y sin datos personales, así que se guarda el CSV
original byte por byte (sin pasar por pandas) junto con su diccionario.
El Censo no cambia; el hash en el manifiesto evita reingerirlo cada mes.
"""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from comun import BRONCE, ahora_utc, descargar, registrar, sha256, ultimo_hash

URL = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_06_cpv2020_csv.zip"
SALIDA = BRONCE / "inegi_censo2020"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "iter_06.zip"
        descargar(URL, zip_path)
        h = sha256(zip_path)
        tam = zip_path.stat().st_size
        if ultimo_hash(URL) == h:
            print("Censo 2020: sin cambios (hash igual), se omite")
            return
        SALIDA.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            datos = next(n for n in z.namelist() if "/conjunto_de_datos/" in n and n.lower().endswith(".csv"))
            dicc = next(n for n in z.namelist() if "/diccionario_datos/" in n and n.lower().endswith(".csv"))
            contenido = z.read(datos)
            (SALIDA / "iter_06_cpv2020.csv").write_bytes(contenido)
            (SALIDA / "diccionario_iter_06_cpv2020.csv").write_bytes(z.read(dicc))
    filas = contenido.count(b"\n") - 1
    registrar({
        "fuente": "INEGI-CENSO2020-ITER",
        "url": URL,
        "fecha_ingesta_utc": ahora_utc(),
        "sha256_origen": h,
        "bytes_origen": tam,
        "archivo_bronce": (SALIDA / "iter_06_cpv2020.csv").relative_to(BRONCE.parent.parent).as_posix(),
        "registros": filas,
    })
    print(f"Censo 2020: {filas} localidades guardadas")


if __name__ == "__main__":
    main()
