"""Verificación de linaje y trazabilidad (E2): Oro -> Plata -> Bronce -> origen.

Comprueba, y falla si algo no cuadra:
  1. Cada fila de cada tabla Oro tiene al menos una entrada en data/oro/linaje_oro.csv.
  2. Cada id_registro del linaje existe en Plata con el mismo archivo y fila de Bronce.
  3. Cada archivo de Bronce citado existe en disco y está en el manifiesto con la
     misma fecha de ingesta (y por tanto con URL de origen y SHA-256).
  4. Re-lectura: para TODOS los registros citados se abre la fila exacta del archivo
     de Bronce y se confirma que el valor crudo (sin espacios) coincide con Plata.
  5. La columna n_registros_fuente de cada fila Oro coincide con su linaje.

Uso:  python src/verificar_linaje.py   (genera docs/E2/verificacion_linaje.md)
"""
from __future__ import annotations

import pandas as pd

from comun import RAIZ, leer_manifiesto

ORO = RAIZ / "data" / "oro"
PLATA = RAIZ / "data" / "plata"
SALIDA = RAIZ / "docs" / "E2" / "verificacion_linaje.md"

TABLAS = {  # tabla Oro -> función que construye su clave igual que en oro.py
    "serie_mensual_colima": lambda d: d["periodo"].astype(str),
    "serie_trimestral_colima": lambda d: d["periodo"].astype(str),
    "factores_suicidio": lambda d: d[["anio", "trimestre", "sexo", "grupo_edad", "zona"]].astype(str).agg("|".join, axis=1),
    "municipios_colima": lambda d: d["cve_mun"].astype(str).str.zfill(3),
    "competencia_centro_colima": lambda d: d["radio_m"].astype(str),
    "consultorios_psicologia_geo": lambda d: d["id_registro"].astype(str),
}
# Columna de Plata que se compara contra Bronce, por prefijo de id_registro
CAMPO_CONTROL = {"EDR": ("defunciones", "causa_def", "causa_def"),
                 "DENUE": ("denue", "clee", "clee"),
                 "CENSO": ("censo2020_municipios", "cve_mun", "MUN")}


def main() -> None:
    lin = pd.read_csv(ORO / "linaje_oro.csv", dtype=str)
    errores: list[str] = []
    filas_md = []

    # 1 y 5: cobertura de cada tabla Oro
    for tabla, clave_fn in TABLAS.items():
        ruta = ORO / f"{tabla}.csv"
        if not ruta.exists():
            continue
        d = pd.read_csv(ruta, dtype=str)
        claves = clave_fn(d)
        l = lin[lin["tabla_oro"] == tabla]
        sin = set(claves) - set(l["clave_oro"])
        conteo = l[l["id_registro"] != "SIN_REGISTROS"].groupby("clave_oro").size()
        dif = (pd.to_numeric(d["n_registros_fuente"]).values != conteo.reindex(claves).fillna(0).values).sum()
        if sin:
            errores.append(f"{tabla}: {len(sin)} filas sin linaje (p. ej. {sorted(sin)[:3]})")
        if dif:
            errores.append(f"{tabla}: {dif} filas con n_registros_fuente distinto al linaje")
        filas_md.append(f"| `{tabla}` | {len(d)} | {len(d) - len(sin)} | {len(l)} | {'OK' if not sin and not dif else 'FALLA'} |")

    # 2: existencia en Plata
    reales = lin[lin["id_registro"] != "SIN_REGISTROS"].drop_duplicates("id_registro")
    reales = reales.assign(prefijo=reales["id_registro"].str.split(":").str[0])
    plata_ok = 0
    releidos = 0
    manif = {(m["archivo_bronce"], m["fecha_ingesta_utc"]) for m in leer_manifiesto()}
    for prefijo, grupo in reales.groupby("prefijo"):
        archivo_plata, col_plata, col_bronce = CAMPO_CONTROL[prefijo]
        p = pd.read_csv(PLATA / f"{archivo_plata}.csv", dtype=str, keep_default_na=False).set_index("id_registro")
        faltan = set(grupo["id_registro"]) - set(p.index)
        if faltan:
            errores.append(f"{prefijo}: {len(faltan)} id_registro del linaje no están en Plata")
        g = grupo[grupo["id_registro"].isin(p.index)]
        pp = p.loc[g["id_registro"]]
        mismo = (pp["archivo_bronce"].values == g["archivo_bronce"].values) & (pp["fila_bronce"].values == g["fila_bronce"].values)
        if not mismo.all():
            errores.append(f"{prefijo}: {(~mismo).sum()} registros con archivo/fila de Bronce distinto entre linaje y Plata")
        plata_ok += int(mismo.sum())

        # 3 y 4: Bronce en disco + manifiesto + re-lectura de la fila exacta
        for archivo, sub in g.groupby("archivo_bronce"):
            ruta = RAIZ / archivo
            if not ruta.exists():
                errores.append(f"No existe el archivo de Bronce {archivo}")
                continue
            for fecha in sub["fecha_ingesta_utc"].unique():
                if (archivo, fecha) not in manif:
                    errores.append(f"{archivo} con fecha {fecha} no está en el manifiesto")
            enc = "utf-8-sig" if prefijo == "CENSO" else "utf-8"
            b = pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding=enc)
            # Se relee la fila que dice PLATA (el linaje ya se comparó contra Plata arriba)
            filas = p.loc[sub["id_registro"], "fila_bronce"].astype(int).values - 2  # fila 1 = encabezado
            en_rango = (filas >= 0) & (filas < len(b))
            if not en_rango.all():
                errores.append(f"{archivo}: {(~en_rango).sum()} filas fuera del rango del archivo")
            crudo = b.iloc[filas[en_rango]][col_bronce].str.strip().values
            limpio = p.loc[sub["id_registro"], col_plata].values[en_rango]
            iguales = crudo == limpio
            releidos += int(iguales.sum())
            if not iguales.all():
                errores.append(f"{archivo}: {(~iguales).sum()} filas no coinciden al releer Bronce")

    rep = ["# Verificación de linaje — E2", "",
           "> Generado por `src/verificar_linaje.py`. Se ejecuta en cada corrida del workflow; si falla, el pipeline se detiene.", "",
           "## Cobertura por tabla Oro", "",
           "| Tabla | Filas | Filas con linaje | Entradas de linaje | Estado |", "|---|---|---|---|---|", *filas_md, "",
           "## Cadena Oro → Plata → Bronce → origen", "",
           f"- Registros fuente distintos citados en el linaje: **{len(reales):,}**",
           f"- Encontrados en Plata con el mismo archivo y fila de Bronce: **{plata_ok:,}**",
           f"- Fila exacta re-leída en Bronce y valor de control idéntico: **{releidos:,}**",
           "- Cada archivo de Bronce está en `data/bronce/manifiesto.csv` con su URL de origen, fecha de ingesta y SHA-256 del archivo descargado.", "",
           "## Resultado", "",
           ("**OK: todas las filas de Oro son rastreables hasta su origen.**" if not errores
            else "**FALLA:**\n\n" + "\n".join(f"- {e}" for e in errores)), ""]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep))
    if errores:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
