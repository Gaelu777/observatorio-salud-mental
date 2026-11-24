"""Diccionario de datos de la capa Oro (E1 Ingeniería de Datos).

Combina dos cosas:
  - lo que dice el código: la descripción, unidad y origen de cada columna
    (escritos a mano abajo);
  - lo que dicen los datos: tipo, % de nulos, mínimo, máximo y un ejemplo
    (se calculan cada vez que corre, así el diccionario no se desactualiza).

Si una columna de Oro no tiene descripción, el script falla. Esto obliga a
documentar cualquier columna nueva antes de que llegue al tablero.

Uso:  python src/diccionario_oro.py
Salida: data/oro/DICCIONARIO.md y data/oro/diccionario_oro.csv
"""
from __future__ import annotations

import re
import sys

import pandas as pd

from comun import RAIZ

ORO = RAIZ / "data" / "oro"

TABLAS = {
    "serie_mensual_colima.csv": "Serie mensual estatal (ene-2018 a dic-2023) de suicidios y defunciones por "
                                "trastornos mentales de residentes de Colima. Base del pronóstico (E1).",
    "serie_trimestral_colima.csv": "La misma serie agregada por trimestre (reducción de datos por agregación).",
    "factores_suicidio.csv": "Conteos de suicidios por año, trimestre, sexo, grupo de edad y zona. Base de los "
                             "factores del experimento y de la comparación de grupos.",
    "municipios_colima.csv": "Una fila por municipio (10): población, oferta de consultorios de psicología y "
                             "tasas de necesidad. Integra EDR + DENUE + Censo 2020.",
    "consultorios_psicologia_geo.csv": "Un registro por consultorio de psicología del DENUE (SCIAN 621331/621332) "
                                       "con coordenadas y distancia al centro de Colima (E2 geoespacial).",
    "competencia_centro_colima.csv": "Consultorios a 500 m, 1 km y 2 km del centro histórico de Colima: la "
                                     "competencia directa de la cliente.",
    "pronostico_suicidio_colima.csv": "Pronóstico de 12 meses del modelo ganador con su intervalo del 95 % "
                                      "(lo genera src/pronostico.py).",
    "localidades_colima.csv": "Una fila por localidad con >= 500 habitantes (65): 8 indicadores del Censo 2020 "
                              "+ distancia al psicólogo más cercano, y sus coordenadas en los componentes "
                              "principales (E3, src/multivariado.py).",
    "linaje_oro.csv": "Tabla puente: cada fila Oro -> cada registro Bronce que la originó (archivo y fila).",
}

# Descripción exacta por nombre de columna: (descripción, unidad / dominio, origen)
COL = {
    "periodo": ("Mes (AAAA-MM) o trimestre (AAAA-Tn) de ocurrencia", "texto", "EDR: anio_ocur + mes_ocurr"),
    "anio": ("Año de ocurrencia de la defunción", "2018-2023", "EDR: anio_ocur"),
    "mes": ("Mes de ocurrencia", "1-12", "EDR: mes_ocurr"),
    "trimestre": ("Trimestre de ocurrencia", "1-4", "Derivado del mes"),
    "semestre": ("Semestre de ocurrencia", "1-2", "Derivado del mes"),
    "suicidio": ("Defunciones de residentes de Colima con causa CIE-10 X60-X84 (lesiones autoinfligidas)",
                 "conteo", "EDR: causa_def, ent_resid=06"),
    "trastorno_mental": ("Defunciones con causa CIE-10 capítulo F (trastornos mentales y del comportamiento)",
                         "conteo", "EDR: causa_def, ent_resid=06"),
    "n_registros_fuente": ("Registros de Bronce que sostienen la fila (ver linaje_oro.csv)", "conteo", "Linaje"),
    "fecha_ingesta_max": ("Fecha UTC de la captura más reciente entre los registros que forman la fila",
                          "ISO 8601", "manifiesto Bronce"),
    "fecha_ingesta_utc": ("Fecha UTC en que se capturó el registro de Bronce", "ISO 8601", "manifiesto Bronce"),
    "sexo": ("Sexo de la persona fallecida (NE = no especificado)", "H / M / NE", "EDR: sexo"),
    "grupo_edad": ("Grupo de edad en años cumplidos (NE = no especificado)", "rangos", "EDR: edad (discretizada)"),
    "zona": ("Zona Metropolitana Colima-Villa de Álvarez (002, 003, 004, 005, 010) vs resto del estado",
             "metropolitana / resto / NE", "Jerarquía municipio -> zona"),
    "suicidios": ("Suicidios en la combinación de factores", "conteo", "EDR"),
    "cve_mun": ("Clave INEGI del municipio (3 dígitos)", "001-010", "DENUE / Censo / EDR"),
    "nom_mun": ("Nombre del municipio", "texto", "Censo 2020"),
    "pobtot": ("Población total 2020", "personas", "Censo 2020 ITER"),
    "suicidios_2018_2023": ("Suicidios de residentes del municipio, 6 años", "conteo", "EDR"),
    "trastornos_mentales_2018_2023": ("Defunciones por trastornos mentales de residentes, 6 años", "conteo", "EDR"),
    "consultorios_psic_privados": ("Consultorios de psicología del sector privado (SCIAN 621331)", "conteo", "DENUE"),
    "consultorios_psic_publicos": ("Consultorios de psicología del sector público (SCIAN 621332)", "conteo", "DENUE"),
    "consultorios_psic": ("Total de consultorios de psicología", "conteo", "DENUE"),
    "consultorios_por_100k": ("Consultorios por cada 100 mil habitantes (indicador de OFERTA)", "tasa", "DENUE / Censo"),
    "tasa_suicidio_anual_100k": ("Suicidios por año por cada 100 mil habitantes (indicador de NECESIDAD)",
                                 "tasa", "EDR / Censo"),
    "tasa_trast_mental_anual_100k": ("Defunciones por trastorno mental por año por 100 mil hab.", "tasa", "EDR / Censo"),
    "oferta_nivel": ("Tercil de consultorios_por_100k", "baja / media / alta", "Discretización por frecuencia"),
    "necesidad_nivel": ("Tercil de tasa_suicidio_anual_100k", "baja / media / alta", "Discretización por frecuencia"),
    "id_registro": ("Identificador de linaje FUENTE:archivo:fila", "texto", "Generado en Plata"),
    "clee": ("Clave Única del Establecimiento del DENUE (identificador público del negocio, no de una persona)",
             "texto", "DENUE"),
    "codigo_act": ("Código SCIAN de la actividad", "621331 privado / 621332 público", "DENUE"),
    "sector": ("Sector del consultorio, derivado del código SCIAN", "privado / publico", "DENUE"),
    "cve_mun_geo": ("Municipio en el que cae el punto según el polígono del Marco Geoestadístico",
                    "001-010", "Unión espacial (GeoPandas)"),
    "ubicacion_consistente": ("True si cve_mun (declarado) = cve_mun_geo (calculado por el punto)",
                              "booleano", "Validación espacial"),
    "per_ocu": ("Rango de personal ocupado del establecimiento", "texto (p. ej. 0 a 5 personas)", "DENUE"),
    "fecha_alta": ("Mes en que el establecimiento se dio de alta en el DENUE", "AAAA-MM", "DENUE"),
    "latitud": ("Latitud WGS84", "grados", "DENUE"),
    "longitud": ("Longitud WGS84", "grados", "DENUE"),
    "distancia_centro_m": ("Distancia en línea recta al Jardín Libertad (centro de Colima), medida en EPSG:6372",
                           "metros", "Cálculo geoespacial"),
    "archivo_bronce": ("Archivo de Bronce del que viene el registro", "ruta", "Linaje"),
    "fila_bronce": ("Número de fila dentro del archivo de Bronce", "entero", "Linaje"),
    "radio_m": ("Radio alrededor del centro de Colima", "500 / 1000 / 2000 m", "Parámetro"),
    "privados": ("Consultorios privados dentro del radio", "conteo", "DENUE"),
    "publicos": ("Consultorios públicos dentro del radio", "conteo", "DENUE"),
    "pct_del_municipio_colima": ("% de los consultorios del municipio de Colima que están dentro del radio",
                                 "%", "Cálculo"),
    "tabla_oro": ("Tabla Oro a la que pertenece la fila", "nombre de tabla", "Linaje"),
    "clave_oro": ("Llave de la fila en esa tabla (periodo, municipio, id...)", "texto", "Linaje"),
    "modelo": ("Modelo de pronóstico ganador (menor RMSE en la prueba 2023)", "texto", "src/pronostico.py"),
    "pronostico": ("Valor esperado del mes", "suicidios", "src/pronostico.py"),
    "limite_inferior_95": ("Límite inferior del intervalo de predicción del 95 % (recortado a 0)",
                           "suicidios", "src/pronostico.py"),
    "limite_superior_95": ("Límite superior del intervalo de predicción del 95 %", "suicidios", "src/pronostico.py"),
    "cve_loc": ("Clave INEGI de la localidad (4 dígitos, única dentro del municipio)", "texto", "Censo 2020 ITER"),
    "nom_loc": ("Nombre de la localidad", "texto", "Censo 2020 ITER"),
    "pct_sin_afiliacion": ("% de la población sin afiliación a servicios de salud", "%", "Censo: PSINDER / POBTOT"),
    "escolaridad_prom": ("Grado promedio de escolaridad de 15 años y más", "años", "Censo: GRAPROES"),
    "pct_60ymas": ("% de la población de 60 años y más", "%", "Censo: P_60YMAS / POBTOT"),
    "pct_condicion_mental": ("% de la población con algún problema o condición mental", "%",
                             "Censo: PCLIM_PMEN / POBTOT"),
    "pct_viv_internet": ("% de viviendas particulares habitadas con internet", "%", "Censo: VPH_INTER / TVIVPARHAB"),
    "pct_desocupacion": ("% de la población económicamente activa desocupada", "%", "Censo: PDESOCUP / PEA"),
    "pct_hogares_jefa": ("% de hogares con persona de referencia mujer", "%", "Censo: HOGJEF_F / TOTHOG"),
    "dist_psicologo_km": ("Distancia en línea recta al consultorio de psicología más cercano (EPSG:6372)",
                          "km", "Unión espacial Censo + DENUE"),
    "log_dist_psicologo": ("log(1 + dist_psicologo_km); reduce el sesgo para el análisis multivariado",
                           "log-km", "Derivado"),
    "mahalanobis2": ("Distancia de Mahalanobis al cuadrado al centroide de las 8 variables "
                     "(> 17.5 = perfil atípico al 97.5 %)", "adimensional", "src/multivariado.py"),
    "cp1": ("Puntaje en CP1 'Urbanización y acceso a psicólogos' (alto = más acceso)", "z", "PCA"),
    "cp2": ("Puntaje en CP2 'Vulnerabilidad del hogar' (alto = más vulnerable)", "z", "PCA"),
    "fuente_entrada": ("Tabla Oro usada para entrenar el modelo", "ruta", "Linaje"),
    "meses_entrenamiento": ("Meses usados para ajustar el modelo final", "entero", "src/pronostico.py"),
}

# Columnas derivadas por sufijo: <base>_<sufijo>
SUFIJOS = {
    "mes_imputado": ("1 si el mes de ocurrencia faltaba y se imputó (ver reporte de limpieza)", "0/1"),
    "atipico_iqr": ("True si queda fuera de [Q1 − 1.5·IQR, Q3 + 1.5·IQR] (marcado, no borrado)", "booleano"),
    "atipico_z_robusto": ("True si |z robusto| > 3.5", "booleano"),
    "z_robusto": ("0.6745·(x − mediana)/MAD", "adimensional"),
    "winsor": ("Valor recortado a los límites IQR (para modelos sensibles a extremos)", "misma unidad"),
    "minmax": ("Normalización min-max a [0, 1]", "0-1"),
    "z": ("Estandarización z-score (media 0, desviación 1)", "adimensional"),
}


def describir(col: str) -> tuple[str, str, str]:
    if col in COL:
        return COL[col]
    for suf, (desc, uni) in SUFIJOS.items():
        m = re.fullmatch(rf"(.+)_{suf}", col)
        if m and m.group(1) in COL:
            return f"{desc} de `{m.group(1)}`", uni, "Derivado en Oro (src/oro.py)"
    raise KeyError(col)


def perfil(s: pd.Series) -> dict:
    nn = s.dropna()
    num = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
    return {
        "tipo": "booleano" if pd.api.types.is_bool_dtype(s) else ("numérico" if num else "texto"),
        "nulos_pct": round(s.isna().mean() * 100, 1),
        "min": (round(float(nn.min()), 4) if num else "") if len(nn) else "",
        "max": (round(float(nn.max()), 4) if num else "") if len(nn) else "",
        "distintos": int(nn.nunique()),
        "ejemplo": str(nn.iloc[0])[:40] if len(nn) else "",
    }


def main() -> None:
    filas, faltan = [], []
    for tabla in TABLAS:
        df = pd.read_csv(ORO / tabla, dtype={"cve_mun": str, "cve_mun_geo": str, "codigo_act": str})
        for c in df.columns:
            try:
                desc, uni, orig = describir(c)
            except KeyError:
                faltan.append(f"{tabla}:{c}")
                continue
            filas.append({"tabla": tabla, "columna": c, "descripcion": desc, "unidad_dominio": uni,
                          "origen": orig, "filas": len(df), **perfil(df[c])})
    if faltan:
        sys.exit("Columnas sin documentar en el diccionario:\n  " + "\n  ".join(faltan))

    d = pd.DataFrame(filas)
    d.to_csv(ORO / "diccionario_oro.csv", index=False)

    md = ["# Diccionario de datos · capa Oro", "",
          "Generado por `src/diccionario_oro.py`; **no editar a mano** (se regenera en cada corrida del pipeline). "
          "Tipo, nulos, mínimo y máximo se miden sobre los datos actuales.", "",
          "El archivo `consultorios_psicologia_colima.geojson` tiene las mismas columnas que "
          "`consultorios_psicologia_geo.csv` más la geometría (punto, EPSG:4326).", "",
          f"**Completitud global (ISO/IEC 25012):** {100 - d['nulos_pct'].mean():.1f} % de celdas no nulas "
          f"en promedio por columna; columnas con algún nulo: {int((d['nulos_pct'] > 0).sum())} de {len(d)}.", ""]
    for tabla, desc in TABLAS.items():
        t = d[d["tabla"] == tabla]
        md += [f"## `{tabla}` ({t['filas'].iloc[0]} filas)", "", desc, "",
               "| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |",
               "|---|---|---|---|---|---|---|---|"]
        for r in t.itertuples():
            md.append(f"| `{r.columna}` | {r.descripcion} | {r.unidad_dominio} | {r.origen} | {r.tipo} | "
                      f"{r.nulos_pct} | {r.min} | {r.max} |")
        md.append("")
    (ORO / "DICCIONARIO.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Diccionario: {len(d)} columnas en {len(TABLAS)} tablas -> data/oro/DICCIONARIO.md")


if __name__ == "__main__":
    main()
