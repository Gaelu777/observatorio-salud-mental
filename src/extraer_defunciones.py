"""Extractor Bronce: Estadística de Defunciones Registradas (EDR), INEGI.

Descarga el conjunto de datos abiertos de cada año, conserva SOLO los registros
relacionados con el estado de Colima (entidad 06 de residencia u ocurrencia) y
los guarda tal cual vienen (todas las columnas, todo como texto, sin limpiar).

Por qué se filtra por Colima en Bronce: el archivo nacional pesa ~230 MB por año
descomprimido; guardarlo en git no es viable. El filtro es una selección de
filas, no una transformación: los valores quedan idénticos al original y el
hash SHA-256 del zip original queda en el manifiesto para poder verificarlo.

Uso:
    python src/extraer_defunciones.py              # años por defecto
    python src/extraer_defunciones.py 2018 2023    # rango explícito
"""
from __future__ import annotations

import sys
import tempfile
import time
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from comun import BRONCE, PAUSA_SEG, ahora_utc, descargar, registrar, sha256, ultimo_hash

URL = ("https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/"
       "{anio}/conjunto_de_datos_defunciones_registradas_{anio}_csv.zip")
ENTIDAD_COLIMA = "06"
ANIO_INICIAL = 2018  # primer año disponible en esta ruta de datos abiertos
SALIDA = BRONCE / "inegi_defunciones"


def procesar_anio(anio: int) -> str:
    url = URL.format(anio=anio)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / f"def_{anio}.zip"
        try:
            descargar(url, zip_path)
        except ValueError:
            return f"{anio}: aún no publicado, se omite"
        h = sha256(zip_path)
        if ultimo_hash(url) == h:
            return f"{anio}: sin cambios (hash igual), se omite"

        with zipfile.ZipFile(zip_path) as z:
            interno = next(n for n in z.namelist()
                           if n.startswith("conjunto_de_datos/") and n.lower().endswith(".csv")
                           and "bitacora" not in n.lower())
            # dtype=str: en Bronce no se interpreta nada (los ceros a la izquierda importan)
            df = pd.read_csv(z.open(interno), dtype=str, encoding="latin-1", keep_default_na=False)
            # Diccionario de datos: se guarda una vez por año como referencia
            dicc = next((n for n in z.namelist() if n.startswith("diccionario_de_datos/")), None)
            if dicc:
                (SALIDA / "diccionarios").mkdir(parents=True, exist_ok=True)
                (SALIDA / "diccionarios" / Path(dicc).name).write_bytes(z.read(dicc))

        # Algunos años traen tabuladores pegados a los valores (p. ej. "06<TAB>"). Solo para
        # FILTRAR se comparan sin espacios; los valores se guardan sin tocar.
        ent_res = df["ent_resid"].str.strip()
        ent_ocu = df["ent_ocurr"].str.strip()
        colima = df[(ent_res == ENTIDAD_COLIMA) | (ent_ocu == ENTIDAD_COLIMA)]
        if colima.empty:
            raise RuntimeError(f"{anio}: 0 registros de Colima; revisar formato del archivo")
        SALIDA.mkdir(parents=True, exist_ok=True)
        archivo = SALIDA / f"defunciones_colima_registradas_{anio}.csv"
        colima.to_csv(archivo, index=False, encoding="utf-8")

        registrar({
            "fuente": "INEGI-EDR",
            "url": url,
            "fecha_ingesta_utc": ahora_utc(),
            "sha256_origen": h,
            "bytes_origen": zip_path.stat().st_size,
            "archivo_bronce": archivo.relative_to(BRONCE.parent.parent).as_posix(),
            "registros": len(colima),
        })
        return f"{anio}: {len(colima)} registros de Colima guardados"


def main() -> None:
    if len(sys.argv) == 3:
        anios = range(int(sys.argv[1]), int(sys.argv[2]) + 1)
    else:
        anios = range(ANIO_INICIAL, date.today().year + 1)
    for i, anio in enumerate(anios):
        if i:
            time.sleep(PAUSA_SEG)
        print(procesar_anio(anio), flush=True)


if __name__ == "__main__":
    main()
