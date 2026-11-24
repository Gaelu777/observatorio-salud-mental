"""Capa Plata: limpieza de tipos y códigos + Puerta de Calidad (Pandera) + cuarentena.

Flujo por fuente:
    Bronce (texto crudo) -> estandarizar (quitar ruido, decodificar códigos, tipar)
    -> Puerta de Calidad (Pandera, validación perezosa) -> válidos a data/plata/
                                                        -> inválidos a data/cuarentena/ con motivo

Reglas:
- Nunca se borra un registro en silencio: cada fila de Bronce termina en Plata o
  en Cuarentena (se verifica al final: objetivo de calidad OC2).
- Un valor DESCONOCIDO declarado por INEGI (mes 99, sexo 9, edad 4998...) NO es
  inválido: es un faltante legítimo, se convierte a nulo y se trata en Oro
  (imputación). Inválido = valor imposible o fuera del catálogo.
- Cada registro lleva su linaje: id_registro, archivo_bronce, fila_bronce,
  fecha_ingesta_utc y sha256_origen (del manifiesto).

Uso:  python src/plata.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors

from comun import RAIZ, leer_manifiesto

PLATA = RAIZ / "data" / "plata"
CUARENTENA = RAIZ / "data" / "cuarentena"
RESUMEN = PLATA / "resumen_plata.json"

MUNICIPIOS_COLIMA = [f"{i:03d}" for i in range(1, 11)]
COLS_LINAJE = ["id_registro", "archivo_bronce", "fila_bronce", "fecha_ingesta_utc", "sha256_origen"]


# --------------------------------------------------------------------------- utilidades
def ultimos_archivos(fuente: str) -> list[dict]:
    """Última ingesta de cada URL de una fuente (según el manifiesto)."""
    por_url: dict[str, dict] = {}
    for fila in leer_manifiesto():
        if fila["fuente"] == fuente:
            por_url[fila["url"]] = fila
    return list(por_url.values())


# Optimización E3: OPTIMIZACION_E3=0 reproduce el comportamiento anterior SOLO para
# medir el "antes" en src/optimizacion.py. En operación normal siempre está activa.
OPTIMIZADO = os.environ.get("OPTIMIZACION_E3", "1") != "0"


def leer_bronce(entrada: dict, prefijo: str, **kw) -> pd.DataFrame:
    ruta = RAIZ / entrada["archivo_bronce"]
    df = pd.read_csv(ruta, dtype=str, keep_default_na=False, **kw)
    df.insert(0, "fila_bronce", np.arange(2, len(df) + 2))  # fila 1 = encabezado
    df.insert(0, "archivo_bronce", entrada["archivo_bronce"])
    if OPTIMIZADO:
        # El nombre del archivo se calcula UNA vez (antes: una vez por fila, 37 mil veces;
        # el perfilador mostró que era el 24 % del tiempo de Plata).
        base = f"{prefijo}:{Path(ruta).stem}:"
        df.insert(0, "id_registro", base + df["fila_bronce"].astype(str))
    else:
        df.insert(0, "id_registro", [f"{prefijo}:{Path(ruta).stem}:{i}" for i in df["fila_bronce"]])
    df["fecha_ingesta_utc"] = entrada["fecha_ingesta_utc"]
    df["sha256_origen"] = entrada["sha256_origen"]
    return df


def quitar_ruido_texto(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Quita espacios/tabuladores al inicio y fin. Devuelve cuántas celdas cambiaron."""
    obj = df.select_dtypes(include="object").columns
    limpio = df[obj].apply(lambda c: c.str.strip())
    cambios = int((limpio != df[obj]).sum().sum())
    df = df.copy()
    df[obj] = limpio
    return df, cambios


def a_entero(serie: pd.Series, desconocidos: tuple[str, ...] = ()) -> pd.Series:
    """Texto -> Int64 nullable; los códigos 'desconocido' de INEGI pasan a nulo."""
    s = serie.replace({c: "" for c in desconocidos}).replace("", np.nan)
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def puerta_calidad(df: pd.DataFrame, esquema: pa.DataFrameSchema, nombre: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida con Pandera en modo perezoso (junta TODOS los errores, no solo el primero).

    Devuelve (válidos, cuarentena). La cuarentena conserva la fila completa más
    la columna `motivo` (columna + regla que falló; varias separadas por ' | ').
    """
    try:
        esquema.validate(df, lazy=True)
        return df, df.iloc[0:0].assign(motivo=pd.Series(dtype=str))
    except SchemaErrors as err:
        fc = err.failure_cases
        # Errores sin índice (p. ej. falta una columna) son estructurales: se detiene todo.
        if fc["index"].isna().any():
            raise RuntimeError(f"[{nombre}] error estructural de esquema:\n{fc[fc['index'].isna()]}") from err
        # Reglas de fila completa (varias columnas): el motivo es solo el nombre de la regla
        de_fila = fc["schema_context"] == "DataFrameSchema"
        fc = fc.assign(motivo=np.where(
            de_fila,
            "regla " + fc["check"].astype(str),
            fc["column"].astype(str) + ": " + fc["check"].astype(str) + " (valor=" + fc["failure_case"].astype(str) + ")"))
        motivos = fc.groupby("index")["motivo"].agg(lambda m: " | ".join(sorted(set(m))))
        malos = df.index.isin(motivos.index)
        cuarentena = df[malos].assign(motivo=motivos.reindex(df.index[malos]).values)
        return df[~malos], cuarentena


def guardar(df: pd.DataFrame, cuarentena: pd.DataFrame, nombre: str) -> None:
    PLATA.mkdir(parents=True, exist_ok=True)
    CUARENTENA.mkdir(parents=True, exist_ok=True)
    df.to_csv(PLATA / f"{nombre}.csv", index=False, encoding="utf-8", lineterminator="\n")
    cuarentena.to_csv(CUARENTENA / f"{nombre}_cuarentena.csv", index=False, encoding="utf-8", lineterminator="\n")


# --------------------------------------------------------------------------- defunciones
# Reducción por selección de variables: de 59-74 columnas se conservan las que
# responden las preguntas analíticas y existen en TODOS los años.
COLS_DEF = ["ent_resid", "mun_resid", "ent_ocurr", "mun_ocurr", "causa_def", "sexo", "edad",
            "dia_ocurr", "mes_ocurr", "anio_ocur", "mes_regis", "anio_regis", "tipo_defun"]

ESQUEMA_DEF = pa.DataFrameSchema(
    {
        "ent_resid": pa.Column(str, pa.Check.str_matches(r"^\d{2}$"), nullable=True),
        "mun_resid": pa.Column(str, pa.Check.str_matches(r"^\d{3}$"), nullable=True),
        "ent_ocurr": pa.Column(str, pa.Check.str_matches(r"^\d{2}$"), nullable=True),
        "mun_ocurr": pa.Column(str, pa.Check.str_matches(r"^\d{3}$"), nullable=True),
        # CIE-10: letra + 2 dígitos + 4º carácter (dígito o X)
        "causa_def": pa.Column(str, pa.Check.str_matches(r"^[A-Z]\d{2}[0-9X]$")),
        "sexo": pa.Column(str, pa.Check.isin(["H", "M"]), nullable=True),
        "edad_anios": pa.Column("Int64", pa.Check.in_range(0, 120), nullable=True),
        "dia_ocurr": pa.Column("Int64", pa.Check.in_range(1, 31), nullable=True),
        "mes_ocurr": pa.Column("Int64", pa.Check.in_range(1, 12), nullable=True),
        "anio_ocur": pa.Column("Int64", pa.Check.in_range(1900, 2100), nullable=True),
        "anio_regis": pa.Column("Int64", pa.Check.in_range(2018, 2100)),
        "mes_regis": pa.Column("Int64", pa.Check.in_range(1, 12)),
        "tipo_defun": pa.Column("Int64", pa.Check.isin([1, 2, 3, 4, 5]), nullable=True),
    },
    checks=[
        # No puede ocurrir después de registrarse
        pa.Check(lambda d: (d["anio_ocur"].isna() | (d["anio_ocur"] <= d["anio_regis"])).fillna(True),
                 element_wise=False, name="ocurrencia<=registro"),
        # Fecha real (no 31 de febrero, etc.)
        pa.Check(lambda d: fecha_valida(d), element_wise=False, name="fecha_ocurrencia_valida"),
    ],
    strict=False,
)


def fecha_valida(d: pd.DataFrame) -> pd.Series:
    completa = d[["anio_ocur", "mes_ocurr", "dia_ocurr"]].notna().all(axis=1)
    f = pd.to_datetime(
        dict(year=d["anio_ocur"].where(completa, 2000), month=d["mes_ocurr"].where(completa, 1),
             day=d["dia_ocurr"].where(completa, 1)), errors="coerce")
    return (~completa) | f.notna()


def decodificar_edad(codigo: pd.Series) -> pd.Series:
    """INEGI codifica la edad en 4 dígitos: 1xxx horas, 2xxx días, 3xxx meses,
    4xxx años, 4998 = no especificada. Menores de 1 año -> 0 años."""
    num = pd.to_numeric(codigo, errors="coerce")
    unidad, valor = num // 1000, num % 1000
    edad = pd.Series(np.where(unidad.isin([1, 2, 3]), 0, np.where(unidad == 4, valor, np.nan)),
                     index=codigo.index)
    edad[num == 4998] = np.nan
    return edad.astype("Int64")


def plata_defunciones() -> dict:
    partes = []
    # Optimización E3 (factor B ganador del experimento de E2): leer solo las columnas
    # que se usan (14 de 59-74). `presunto` es el nombre viejo de `tipo_defun` (2018-2021).
    necesarias = set(COLS_DEF) | {"presunto"}
    usecols = (lambda c: c in necesarias) if OPTIMIZADO else None
    for e in sorted(ultimos_archivos("INEGI-EDR"), key=lambda e: e["archivo_bronce"]):
        df = leer_bronce(e, "EDR", usecols=usecols)
        # Conflicto de esquema: 2018-2021 llaman `presunto` a lo que 2022+ llama `tipo_defun`
        # (mismo catálogo: 1 accidente, 2 homicidio, 3 suicidio, 4 natural/enfermedad, 5 otra).
        if "tipo_defun" not in df.columns and "presunto" in df.columns:
            df = df.rename(columns={"presunto": "tipo_defun"})
        partes.append(df[COLS_LINAJE[:3] + COLS_DEF + COLS_LINAJE[3:]])
    bronce = pd.concat(partes, ignore_index=True)
    n_bronce = len(bronce)
    df, celdas_ruido = quitar_ruido_texto(bronce)

    # Códigos de "no especificado" de INEGI -> nulo (faltante legítimo, no error)
    df["ent_resid"] = df["ent_resid"].replace({"99": np.nan})
    df["mun_resid"] = df["mun_resid"].replace({"999": np.nan})
    df["ent_ocurr"] = df["ent_ocurr"].replace({"99": np.nan})
    df["mun_ocurr"] = df["mun_ocurr"].replace({"999": np.nan})
    df["sexo"] = df["sexo"].map({"1": "H", "2": "M", "9": np.nan}).where(df["sexo"].isin(["1", "2", "9"]), df["sexo"])
    df["edad_anios"] = decodificar_edad(df["edad"])
    df["dia_ocurr"] = a_entero(df["dia_ocurr"], ("99",))
    df["mes_ocurr"] = a_entero(df["mes_ocurr"], ("99",))
    df["anio_ocur"] = a_entero(df["anio_ocur"], ("9999",))
    df["mes_regis"] = a_entero(df["mes_regis"])
    df["anio_regis"] = a_entero(df["anio_regis"])
    df["tipo_defun"] = a_entero(df["tipo_defun"], ("8", "9"))
    df = df.drop(columns=["edad"]).rename(columns={})

    validos, cuarentena = puerta_calidad(df, ESQUEMA_DEF, "defunciones")
    guardar(validos, cuarentena, "defunciones")
    return {"bronce": n_bronce, "plata": len(validos), "cuarentena": len(cuarentena),
            "celdas_con_ruido_corregidas": celdas_ruido}


# --------------------------------------------------------------------------- DENUE
PER_OCU = {"0 a 5 personas": (0, 5), "6 a 10 personas": (6, 10), "11 a 30 personas": (11, 30),
           "31 a 50 personas": (31, 50), "51 a 100 personas": (51, 100),
           "101 a 250 personas": (101, 250), "251 y más personas": (251, np.nan)}

ESQUEMA_DENUE = pa.DataFrameSchema(
    {
        "clee": pa.Column(str, pa.Check.str_length(1, 60), unique=True, report_duplicates="exclude_first"),
        "codigo_act": pa.Column(str, pa.Check.str_matches(r"^621\d{3}$")),
        "cve_ent": pa.Column(str, pa.Check.eq("06")),
        "cve_mun": pa.Column(str, pa.Check.isin(MUNICIPIOS_COLIMA)),
        "per_ocu": pa.Column(str, pa.Check.isin(list(PER_OCU))),
        # Colima continental (se excluye el archipiélago de Revillagigedo)
        "latitud": pa.Column(float, pa.Check.in_range(18.6, 19.6)),
        "longitud": pa.Column(float, pa.Check.in_range(-104.8, -103.4)),
        "fecha_alta": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}$")),
    },
    strict=False,
)


def plata_denue() -> dict:
    e = sorted(ultimos_archivos("INEGI-DENUE"), key=lambda e: e["fecha_ingesta_utc"])[-1]
    bronce = leer_bronce(e, "DENUE")
    df, ruido = quitar_ruido_texto(bronce)
    df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
    validos, cuarentena = puerta_calidad(df, ESQUEMA_DENUE, "denue")
    validos = validos.assign(
        es_psicologia=validos["codigo_act"].isin(["621331", "621332"]),
        sector=np.where(validos["codigo_act"].str.endswith("2"), "publico", "privado"),
        per_ocu_min=validos["per_ocu"].map(lambda v: PER_OCU[v][0]),
        per_ocu_max=validos["per_ocu"].map(lambda v: PER_OCU[v][1]),
    )
    guardar(validos, cuarentena, "denue")
    return {"bronce": len(bronce), "plata": len(validos), "cuarentena": len(cuarentena),
            "celdas_con_ruido_corregidas": ruido}


# --------------------------------------------------------------------------- Censo 2020
COLS_CENSO = ["POBTOT", "POBFEM", "POBMAS", "P_15YMAS", "P_15A17", "P_18A24", "P_18YMAS", "P_60YMAS"]

ESQUEMA_CENSO = pa.DataFrameSchema(
    {
        "cve_mun": pa.Column(str, pa.Check.isin(MUNICIPIOS_COLIMA), unique=True),
        **{c.lower(): pa.Column("Int64", pa.Check.ge(0)) for c in COLS_CENSO},
    },
    checks=[
        pa.Check(lambda d: d["pobfem"] + d["pobmas"] == d["pobtot"], element_wise=False, name="fem+mas=total"),
        pa.Check(lambda d: d["p_15ymas"] <= d["pobtot"], element_wise=False, name="15ymas<=total"),
    ],
    strict=False,
)


def plata_censo() -> dict:
    e = ultimos_archivos("INEGI-CENSO2020-ITER")[-1]
    bronce = leer_bronce(e, "CENSO", encoding="utf-8-sig")
    df, ruido = quitar_ruido_texto(bronce)
    # El ITER mezcla niveles en una sola tabla: total estatal (MUN=000), totales
    # municipales (LOC=0000) y localidades. Se toma el total municipal como cifra
    # oficial; sumar localidades daría menos, porque INEGI reserva con "*" los
    # datos de localidades de 1-2 viviendas por confidencialidad.
    es_municipal = (df["LOC"] == "0000") & (df["MUN"] != "000")
    otros_niveles = df[~es_municipal]
    df = df[es_municipal].rename(columns={"MUN": "cve_mun", "NOM_MUN": "nom_mun"})
    for c in COLS_CENSO:
        df[c.lower()] = a_entero(df[c], ("*", "N/D"))
    df = df[COLS_LINAJE[:3] + ["cve_mun", "nom_mun"] + [c.lower() for c in COLS_CENSO] + COLS_LINAJE[3:]]
    validos, cuarentena = puerta_calidad(df, ESQUEMA_CENSO, "censo")
    guardar(validos, cuarentena, "censo2020_municipios")
    return {"bronce": len(bronce), "plata": len(validos), "cuarentena": len(cuarentena),
            "fuera_de_alcance_no_municipal": len(otros_niveles), "celdas_con_ruido_corregidas": ruido}


# --------------------------------------------------------------------------- main
def main() -> None:
    resumen = {"defunciones": plata_defunciones(), "denue": plata_denue(), "censo2020": plata_censo()}
    # OC2: cero pérdida silenciosa
    for nombre, r in resumen.items():
        cuadra = r["bronce"] == r["plata"] + r["cuarentena"] + r.get("fuera_de_alcance_no_municipal", 0)
        r["oc2_sin_perdida"] = bool(cuadra)
        if not cuadra:
            raise RuntimeError(f"[{nombre}] se perdieron registros: {r}")
    RESUMEN.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
