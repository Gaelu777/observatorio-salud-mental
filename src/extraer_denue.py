"""Extractor Bronce: DENUE (Directorio Estadístico Nacional de Unidades Económicas), INEGI.

Descarga masiva del estado de Colima (sin token; ruta permitida por robots.txt).
Conserva los establecimientos del subsector SCIAN 621 (servicios médicos de
consulta externa), que incluye:
    621331  Consultorios de psicología del sector privado
    621332  Consultorios de psicología del sector público

MINIMIZACIÓN DE DATOS PERSONALES (excepción documentada a "Bronce = crudo"):
Muchos consultorios están registrados a nombre de una persona física, así que el
nombre, razón social, teléfono, correo y web SÍ son datos personales. Esas
columnas se eliminan ANTES de escribir a disco; el resto queda idéntico al
original. El hash del zip original queda en el manifiesto.

DENUE es una "foto" del momento: cada ejecución con cambios genera un archivo
nuevo fechado, lo que permite ver altas/bajas entre ediciones.
"""
from __future__ import annotations

import tempfile
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from comun import BRONCE, ahora_utc, descargar, guardar_huella, registrar, sha256, sin_cambios, ultimo_hash

URL = "https://www.inegi.org.mx/contenidos/masiva/denue/denue_06_csv.zip"
SALIDA = BRONCE / "inegi_denue"
COLUMNAS_PERSONALES = ["nom_estab", "raz_social", "telefono", "correoelec", "www"]
PREFIJO_SCIAN = "621"


def main() -> None:
    igual, huella = sin_cambios(URL)
    if igual:
        print("DENUE: sin cambios (mismo ETag y tamaño), no se descarga")
        return
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "denue_06.zip"
        descargar(URL, zip_path)
        h = sha256(zip_path)
        tam = zip_path.stat().st_size
        if ultimo_hash(URL) == h:
            guardar_huella(URL, huella)
            print("DENUE: sin cambios (hash igual), se omite")
            return
        with zipfile.ZipFile(zip_path) as z:
            interno = next(n for n in z.namelist()
                           if n.startswith("conjunto_de_datos/") and n.lower().endswith(".csv"))
            df = pd.read_csv(z.open(interno), dtype=str, encoding="latin-1", keep_default_na=False)

    df = df[df["codigo_act"].str.startswith(PREFIJO_SCIAN)]
    df = df.drop(columns=[c for c in COLUMNAS_PERSONALES if c in df.columns])

    SALIDA.mkdir(parents=True, exist_ok=True)
    archivo = SALIDA / f"denue_colima_scian621_{date.today():%Y%m%d}.csv"
    df.to_csv(archivo, index=False, encoding="utf-8", lineterminator="\n")
    registrar({
        "fuente": "INEGI-DENUE",
        "url": URL,
        "fecha_ingesta_utc": ahora_utc(),
        "sha256_origen": h,
        "bytes_origen": tam,
        "archivo_bronce": archivo.relative_to(BRONCE.parent.parent).as_posix(),
        "registros": len(df),
    })
    guardar_huella(URL, huella)
    psic = df["codigo_act"].isin(["621331", "621332"]).sum()
    print(f"DENUE: {len(df)} establecimientos SCIAN 621 ({psic} de psicología) guardados")


if __name__ == "__main__":
    main()
