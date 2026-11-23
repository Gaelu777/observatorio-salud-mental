"""Capa Oro: preprocesamiento estadístico e integración de fuentes.

Entradas: data/plata/{defunciones,denue,censo2020_municipios}.csv
Salidas (data/oro/):
    serie_mensual_colima.csv     72 meses, variable a pronosticar (E1/E3 del proyecto)
    serie_trimestral_colima.csv  reducción por agregación
    factores_suicidio.csv        conteos por año, trimestre, sexo, grupo de edad y zona (E2)
    municipios_colima.csv        integración necesidad (EDR) + oferta (DENUE) + población (Censo)
    linaje_oro.csv               cada fila de Oro -> registros de Plata -> archivo/fila de Bronce
Reporte: docs/E1/reporte_limpieza.md (se regenera con cada corrida, con las cifras reales)

Uso:  python src/oro.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from comun import RAIZ, leer_manifiesto

PLATA = RAIZ / "data" / "plata"
ORO = RAIZ / "data" / "oro"
REPORTE = RAIZ / "docs" / "E1" / "reporte_limpieza.md"
SEMILLA = 42
ANIOS = range(2018, 2024)  # ventana con años de registro completos

# Zona Metropolitana Colima–Villa de Álvarez (delimitación SEDATU-CONAPO-INEGI)
ZM_COLIMA = {"002", "010", "003", "004", "005"}  # Colima, V. de Álvarez, Comala, Coquimatlán, Cuauhtémoc
# Grupos de edad compatibles con lo que publica el Censo (para poder calcular tasas)
CORTES_EDAD = [0, 15, 25, 60, 200]
ETIQ_EDAD = ["0-14", "15-24", "25-59", "60+"]

lineas_reporte: list[str] = []


def rep(texto: str = "") -> None:
    lineas_reporte.append(texto)


def tabla_md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    filas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        filas.append("| " + " | ".join("" if pd.isna(v) else (f"{v:.3f}" if isinstance(v, float) else str(v))
                                         for v in r.values) + " |")
    return "\n".join(filas)


def guardar(df: pd.DataFrame, nombre: str) -> None:
    ORO.mkdir(parents=True, exist_ok=True)
    df.to_csv(ORO / nombre, index=False, encoding="utf-8", lineterminator="\n")


# --------------------------------------------------------------------------- carga
def cargar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    d = pd.read_csv(PLATA / "defunciones.csv", dtype=str, keep_default_na=False).replace("", np.nan)
    for c in ["edad_anios", "dia_ocurr", "mes_ocurr", "anio_ocur", "mes_regis", "anio_regis", "tipo_defun"]:
        d[c] = pd.to_numeric(d[c]).astype("Int64")
    den = pd.read_csv(PLATA / "denue.csv", dtype=str, keep_default_na=False)
    den["es_psicologia"] = den["es_psicologia"] == "True"
    cen = pd.read_csv(PLATA / "censo2020_municipios.csv", dtype={"cve_mun": str})
    return d, den, cen


# --------------------------------------------------------------------------- jerarquías conceptuales
def jerarquias(d: pd.DataFrame) -> pd.DataFrame:
    """Causa:  código CIE-10 (X700) -> categoría (X70) -> grupo analítico -> capítulo (X)
    Lugar:  municipio -> zona (metropolitana / resto) -> estado
    Edad:   años -> grupo de edad (discretización por cortes compatibles con el Censo)
    Tiempo: día -> mes -> trimestre -> año (se aplica después de imputar el mes)"""
    d = d.copy()
    d["cie_categoria"] = d["causa_def"].str[:3]
    d["cie_capitulo"] = d["causa_def"].str[0]
    es_suicidio = d["cie_categoria"].between("X60", "X84")
    es_mental = d["cie_capitulo"] == "F"
    d["grupo_causa"] = np.select([es_suicidio, es_mental], ["suicidio", "trastorno_mental"], "otra")
    d["zona"] = np.where(d["mun_resid"].isin(ZM_COLIMA), "metropolitana", "resto")
    d.loc[d["mun_resid"].isna(), "zona"] = np.nan
    d["grupo_edad"] = pd.cut(d["edad_anios"].astype(float), CORTES_EDAD, right=False, labels=ETIQ_EDAD)
    return d


# --------------------------------------------------------------------------- faltantes
def diagnostico_faltantes(r: pd.DataFrame) -> None:
    """¿El mes de ocurrencia falta al azar?
    - MCAR: la probabilidad de faltar no depende de nada.
    - MAR: depende de variables OBSERVADAS (se puede probar).
    - MNAR: depende del propio valor faltante (no se puede probar con los datos; se argumenta).
    Prueba: chi-cuadrada de independencia entre "falta el mes" y cada variable observada.
    Si alguna asociación es significativa, se rechaza MCAR."""
    rep("## 1. Valores faltantes")
    rep()
    vars_falt = {"mes_ocurr": "mes de ocurrencia", "anio_ocur": "año de ocurrencia", "sexo": "sexo",
                 "edad_anios": "edad", "mun_resid": "municipio de residencia", "dia_ocurr": "día de ocurrencia"}
    t = pd.DataFrame({"variable": list(vars_falt.values()),
                      "faltantes": [int(r[c].isna().sum()) for c in vars_falt],
                      "pct": [100 * r[c].isna().mean() for c in vars_falt]})
    rep(f"Residentes de Colima en Plata: **{len(r):,}** defunciones. Faltantes por variable (códigos *no especificado* de INEGI convertidos a nulo en Plata):")
    rep()
    rep(tabla_md(t))
    rep()

    falta = r["mes_ocurr"].isna()
    violenta = r["tipo_defun"].isin([1, 2, 3]).map({True: "violenta", False: "no_violenta"})
    pruebas = {
        "tipo de defunción (violenta / no violenta)": violenta,
        "sexo": r["sexo"].fillna("NE"),
        "grupo de edad": r["grupo_edad"].astype(str).replace("nan", "NE"),
        "zona": r["zona"].fillna("NE"),
        "año de registro": r["anio_regis"].astype(str),
    }
    filas = []
    for nombre, var in pruebas.items():
        ct = pd.crosstab(var, falta)
        if ct.shape[1] < 2:
            continue
        chi2, p, gl, _ = chi2_contingency(ct)
        pct = (ct[True] / ct.sum(axis=1) * 100).round(2).to_dict()
        filas.append({"variable observada": nombre, "chi2": round(chi2, 1), "gl": gl, "p": p,
                      "% sin mes por nivel": ", ".join(f"{k}: {v}%" for k, v in pct.items())})
    tp = pd.DataFrame(filas)
    rep("### Diagnóstico del mecanismo para *mes de ocurrencia*")
    rep()
    rep(tabla_md(tp))
    rep()
    hay_asociacion = (tp["p"] < 0.05).any()
    rep(f"**Conclusión:** {'se rechaza MCAR' if hay_asociacion else 'no se rechaza MCAR'} (α = 0.05). "
        + ("La falta del mes se asocia con variables observadas, principalmente con el tipo de defunción: "
           "las muertes violentas pierden la fecha con mucha más frecuencia, porque el cuerpo a veces se "
           "encuentra días después y el médico legista no puede fijar la fecha. Esto es **MAR** respecto al "
           "tipo de defunción. Además hay un componente **MNAR** que no se puede probar: cuanto más tiempo "
           "pasa sin encontrar el cuerpo, más probable es que se desconozca justo el mes. También se observa "
           "**faltante conjunto**: cuando falta la edad (NE), casi la mitad de esos registros tampoco tiene mes; "
           "son casos de cuerpos no identificados." if hay_asociacion
           else "No hay evidencia de asociación con variables observadas."))
    rep()
    rep("**Tratamiento:**")
    rep("- *Año desconocido* → se imputa con el **año de registro**, que coincide con el de ocurrencia en "
        f"{100 * (r['anio_ocur'] == r['anio_regis']).sum() / r['anio_ocur'].notna().sum():.1f} % de los casos con año conocido (imputación condicional determinista).")
    rep("- *Mes desconocido* → **hot-deck condicional**: a cada registro se le asigna un mes sorteado de la "
        "distribución observada de su mismo grupo de causa (suicidio / trastorno mental / otra). Como el "
        "mecanismo es MAR por tipo de causa, imputar por grupo de causa es lo que corrige el sesgo; imputar "
        f"con la moda inflaría artificialmente un solo mes. Semilla fija = {SEMILLA} (reproducible). Cada registro "
        "queda marcado con `mes_imputado = True`.")
    rep("- *Sexo / edad / municipio desconocidos* → **no se imputan**: son pocos casos y se reportan como "
        "categoría *No especificado* en las tablas de factores. Imputarlos inventaría información demográfica.")
    rep("- *Meses sin defunciones* → son **ceros reales**, no faltantes: la malla mensual se completa con 0.")
    rep()


def imputar(r: pd.DataFrame) -> pd.DataFrame:
    r = r.copy()
    rng = np.random.default_rng(SEMILLA)
    r["anio_imputado"] = r["anio_ocur"].isna()
    r["anio_ocur"] = r["anio_ocur"].fillna(r["anio_regis"])
    r["mes_imputado"] = r["mes_ocurr"].isna()
    for grupo, sub in r.groupby("grupo_causa"):
        conocidos = sub["mes_ocurr"].dropna().astype(int)
        probs = conocidos.value_counts(normalize=True).sort_index()
        idx = sub.index[sub["mes_ocurr"].isna()]
        if len(idx):
            r.loc[idx, "mes_ocurr"] = rng.choice(probs.index.to_numpy(), size=len(idx), p=probs.to_numpy())
    r["mes_ocurr"] = r["mes_ocurr"].astype(int)
    r["anio_ocur"] = r["anio_ocur"].astype(int)
    r["periodo"] = pd.PeriodIndex.from_fields(year=r["anio_ocur"], month=r["mes_ocurr"], freq="M").astype(str)
    r["trimestre"] = (r["mes_ocurr"] - 1) // 3 + 1
    return r


# --------------------------------------------------------------------------- atípicos y escalamiento
def marcar_atipicos(s: pd.Series) -> pd.DataFrame:
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    lim_sup, lim_inf = q3 + 1.5 * iqr, q1 - 1.5 * iqr
    med = s.median()
    mad = (s - med).abs().median()
    z_rob = 0.6745 * (s - med) / mad if mad else pd.Series(0.0, index=s.index)
    return pd.DataFrame({
        "atipico_iqr": (s > lim_sup) | (s < lim_inf),
        "z_robusto": z_rob.round(3),
        "atipico_z_robusto": z_rob.abs() > 3.5,
        "winsor": s.clip(lower=max(lim_inf, 0), upper=lim_sup),
    }), (lim_inf, lim_sup, med, mad)


def escalar(s: pd.Series) -> pd.DataFrame:
    rango = s.max() - s.min()
    return pd.DataFrame({
        "minmax": ((s - s.min()) / rango).round(4) if rango else 0.0,
        "z": ((s - s.mean()) / s.std(ddof=1)).round(4),
    })


# --------------------------------------------------------------------------- linaje
def linaje(tabla: str, clave: pd.Series, registros: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"tabla_oro": tabla, "clave_oro": clave.values,
                         "id_registro": registros["id_registro"].values,
                         "archivo_bronce": registros["archivo_bronce"].values,
                         "fila_bronce": registros["fila_bronce"].values,
                         "fecha_ingesta_utc": registros["fecha_ingesta_utc"].values})


def linaje_cero(tabla: str, claves: list[str]) -> pd.DataFrame:
    """Filas de Oro con conteo 0 no tienen registros fuente; su linaje apunta a
    TODOS los archivos de Bronce de defunciones que se revisaron para concluir
    que no hubo casos (un cero también es un dato que debe ser trazable)."""
    edr = [f for f in leer_manifiesto() if f["fuente"] == "INEGI-EDR"]
    archivos = ";".join(sorted({f["archivo_bronce"] for f in edr}))
    fecha = max(f["fecha_ingesta_utc"] for f in edr)
    return pd.DataFrame({"tabla_oro": tabla, "clave_oro": claves, "id_registro": "SIN_REGISTROS",
                         "archivo_bronce": archivos, "fila_bronce": pd.NA, "fecha_ingesta_utc": fecha})


def resumen_linaje(regs: pd.DataFrame, clave: str) -> pd.DataFrame:
    return regs.groupby(clave).agg(n_registros_fuente=("id_registro", "size"),
                                   fecha_ingesta_max=("fecha_ingesta_utc", "max"))


# --------------------------------------------------------------------------- series
def series(r: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    sm = r[r["grupo_causa"].isin(["suicidio", "trastorno_mental"]) & r["anio_ocur"].isin(ANIOS)]
    malla = pd.period_range(f"{min(ANIOS)}-01", f"{max(ANIOS)}-12", freq="M").astype(str)
    conteo = (sm.pivot_table(index="periodo", columns="grupo_causa", values="id_registro",
                             aggfunc="count", fill_value=0)
              .reindex(malla, fill_value=0))  # meses sin casos = 0 real
    imp = sm[sm["mes_imputado"]].groupby(["periodo", "grupo_causa"]).size().unstack(fill_value=0).reindex(malla, fill_value=0)
    mensual = pd.DataFrame({"periodo": malla})
    mensual["anio"] = mensual["periodo"].str[:4].astype(int)
    mensual["mes"] = mensual["periodo"].str[5:].astype(int)
    mensual["trimestre"] = (mensual["mes"] - 1) // 3 + 1
    mensual["semestre"] = np.where(mensual["mes"] <= 6, 1, 2)
    rep("## 2. Atípicos y ruido")
    rep()
    rep("Se aplican **IQR** (Tukey, 1.5·IQR) y **Z robusto** (0.6745·(x − mediana)/MAD, umbral 3.5) a los "
        "conteos mensuales. No se usa el Z clásico porque la media y la desviación estándar se ven "
        "afectadas por el mismo valor atípico que se busca. Isolation Forest tampoco tiene sentido para una "
        "sola variable con 72 datos.")
    rep()
    rep("**Tratamiento:** los atípicos **no se borran**, porque son muertes reales. Se marcan y se crea una "
        "versión *winsorizada* (recortada al límite superior del IQR) para modelos sensibles a valores extremos. "
        "El pronóstico debe compararse con y sin winsorizar.")
    rep()
    filas_at = []
    for g in ["suicidio", "trastorno_mental"]:
        s = conteo[g].astype(float).values
        s = pd.Series(s)
        mensual[g] = s.astype(int).values
        mensual[f"{g}_mes_imputado"] = imp[g].values if g in imp else 0
        at, (li, ls, med, mad) = marcar_atipicos(s)
        for c in at.columns:
            mensual[f"{g}_{c}"] = at[c].values
        esc = escalar(s)
        mensual[f"{g}_minmax"] = esc["minmax"].values
        mensual[f"{g}_z"] = esc["z"].values
        marcados = mensual.loc[at["atipico_iqr"].values | at["atipico_z_robusto"].values, ["periodo", g]]
        filas_at.append({"serie": g, "mediana": med, "MAD": mad, "límite IQR": f"[{max(li, 0):.1f}, {ls:.1f}]",
                         "atípicos IQR": int(at["atipico_iqr"].sum()), "atípicos Z robusto": int(at["atipico_z_robusto"].sum()),
                         "meses marcados": ", ".join(f"{p} ({v})" for p, v in marcados.values) or "ninguno"})
    rep(tabla_md(pd.DataFrame(filas_at)))
    rep()
    rep("Ruido de captura: los archivos 2018–2021 traen tabuladores pegados a los valores (`\"06\\t\"`). Se "
        "quitaron en Plata; el conteo exacto de celdas corregidas está en `data/plata/resumen_plata.json`.")
    rep()

    lin = []
    res = resumen_linaje(sm, "periodo").reindex(malla)
    mensual["n_registros_fuente"] = res["n_registros_fuente"].fillna(0).astype(int).values
    mensual["fecha_ingesta_max"] = res["fecha_ingesta_max"].values
    lin.append(linaje("serie_mensual_colima", sm["periodo"], sm))
    ceros = mensual.loc[mensual["n_registros_fuente"] == 0, "periodo"].tolist()
    if ceros:
        lc = linaje_cero("serie_mensual_colima", ceros)
        lin.append(lc)
        mensual.loc[mensual["periodo"].isin(ceros), "fecha_ingesta_max"] = lc["fecha_ingesta_utc"].iloc[0]

    # Reducción por agregación: mensual -> trimestral
    sm = sm.assign(periodo_t=sm["anio_ocur"].astype(str) + "-T" + sm["trimestre"].astype(str))
    trim = (mensual.groupby(["anio", "trimestre"], as_index=False)[["suicidio", "trastorno_mental"]].sum())
    trim.insert(0, "periodo", trim["anio"].astype(str) + "-T" + trim["trimestre"].astype(str))
    for g in ["suicidio", "trastorno_mental"]:
        esc = escalar(trim[g].astype(float))
        trim[f"{g}_minmax"], trim[f"{g}_z"] = esc["minmax"], esc["z"]
    rt = resumen_linaje(sm, "periodo_t").reindex(trim["periodo"])
    trim["n_registros_fuente"] = rt["n_registros_fuente"].fillna(0).astype(int).values
    trim["fecha_ingesta_max"] = rt["fecha_ingesta_max"].values
    lin.append(linaje("serie_trimestral_colima", sm["periodo_t"], sm))
    ceros_t = trim.loc[trim["n_registros_fuente"] == 0, "periodo"].tolist()
    if ceros_t:
        lin.append(linaje_cero("serie_trimestral_colima", ceros_t))
    guardar(mensual, "serie_mensual_colima.csv")
    guardar(trim, "serie_trimestral_colima.csv")
    return mensual, lin


# --------------------------------------------------------------------------- factores (E2)
def factores(r: pd.DataFrame) -> list[pd.DataFrame]:
    s = r[(r["grupo_causa"] == "suicidio") & r["anio_ocur"].isin(ANIOS)].copy()
    s["sexo"] = s["sexo"].fillna("NE")
    s["grupo_edad"] = s["grupo_edad"].astype(str).replace("nan", "NE")
    s["zona"] = s["zona"].fillna("NE")
    claves = ["anio_ocur", "trimestre", "sexo", "grupo_edad", "zona"]
    s["clave"] = s[claves].astype(str).agg("|".join, axis=1)
    f = s.groupby(claves, as_index=False).agg(suicidios=("id_registro", "size"),
                                              n_registros_fuente=("id_registro", "size"),
                                              fecha_ingesta_max=("fecha_ingesta_utc", "max"))
    f = f.rename(columns={"anio_ocur": "anio"})
    guardar(f, "factores_suicidio.csv")
    return [linaje("factores_suicidio", s["clave"], s)]


# --------------------------------------------------------------------------- integración municipal
def municipios(r: pd.DataFrame, den: pd.DataFrame, cen: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    rep("## 3. Integración de fuentes heterogéneas")
    rep()
    rep("| Conflicto | Fuente(s) | Resolución |")
    rep("|---|---|---|")
    rep("| Mismo dato con nombre distinto: `presunto` (2018–2021) vs `tipo_defun` (2022+) | EDR | Se renombra a `tipo_defun` (mismo catálogo) en Plata |")
    rep("| Número de columnas distinto por año (59 vs 73–74) | EDR | Selección de las 13 variables presentes en todos los años |")
    rep("| Llave de municipio: `mun_resid` (EDR), `cve_mun` (DENUE), `MUN` (Censo) | las 3 | Llave única `cve_mun` texto de 3 dígitos con ceros a la izquierda |")
    rep("| Codificación de texto: DENUE en Latin-1, Censo en UTF-8 con BOM, EDR solo códigos | DENUE, Censo | Todo se escribe en UTF-8; los nombres oficiales de municipio salen del Censo |")
    rep("| Niveles mezclados en una tabla (estado, municipio, localidad) | Censo | Solo se toman los totales municipales (`LOC=0000`) |")
    rep("| Valores reservados `*` por confidencialidad | Censo | Nulo (no cero); los totales municipales no los tienen |")
    rep("| Personal ocupado como rango de texto (`0 a 5 personas`) | DENUE | Se separa en `per_ocu_min` / `per_ocu_max` numéricos |")
    rep("| Granularidad temporal: EDR mensual 2018–2023, Censo fijo 2020, DENUE foto 2026 | las 3 | Tasas con población 2020 como denominador (punto medio del periodo); la oferta se trata como actual. Se declara como limitación |")

    # Conflicto de definición: causa CIE-10 vs variable "tipo de defunción"
    a = r["grupo_causa"] == "suicidio"
    b = r["tipo_defun"] == 3
    rep(f"| Dos campos para \"suicidio\": causa CIE-10 X60–X84 vs `tipo_defun = 3` | EDR | Coinciden en {int((a & b).sum())} casos; "
        f"{int((a & ~b).sum())} solo por CIE-10 y {int((~a & b).sum())} solo por tipo. Prevalece la **causa básica CIE-10**, que es la causa certificada y la definición estándar de la OMS |")
    rep()

    s = r[r["grupo_causa"].isin(["suicidio", "trastorno_mental"]) & r["anio_ocur"].isin(ANIOS) & r["mun_resid"].notna()]
    conteos = s.pivot_table(index="mun_resid", columns="grupo_causa", values="id_registro", aggfunc="count", fill_value=0)
    psic = den[den["es_psicologia"]]
    oferta = psic.pivot_table(index="cve_mun", columns="sector", values="id_registro", aggfunc="count", fill_value=0)
    m = cen[["cve_mun", "nom_mun", "pobtot", "id_registro"]].rename(columns={"id_registro": "id_censo"}).set_index("cve_mun")
    m = m.join(conteos).join(oferta).fillna(0).reset_index()
    for c in ["suicidio", "trastorno_mental", "privado", "publico"]:
        if c not in m:
            m[c] = 0
        m[c] = m[c].astype(int)
    m = m.rename(columns={"privado": "consultorios_psic_privados", "publico": "consultorios_psic_publicos",
                          "suicidio": "suicidios_2018_2023", "trastorno_mental": "trastornos_mentales_2018_2023"})
    n_anios = len(ANIOS)
    m["consultorios_psic"] = m["consultorios_psic_privados"] + m["consultorios_psic_publicos"]
    m["consultorios_por_100k"] = (m["consultorios_psic"] / m["pobtot"] * 1e5).round(2)
    m["tasa_suicidio_anual_100k"] = (m["suicidios_2018_2023"] / n_anios / m["pobtot"] * 1e5).round(2)
    m["tasa_trast_mental_anual_100k"] = (m["trastornos_mentales_2018_2023"] / n_anios / m["pobtot"] * 1e5).round(2)
    m["zona"] = np.where(m["cve_mun"].isin(ZM_COLIMA), "metropolitana", "resto")

    # Normalización / estandarización de las variables continuas
    for c in ["consultorios_por_100k", "tasa_suicidio_anual_100k", "tasa_trast_mental_anual_100k", "pobtot"]:
        esc = escalar(m[c].astype(float))
        m[f"{c}_minmax"], m[f"{c}_z"] = esc["minmax"].values, esc["z"].values

    # Discretización: terciles (misma frecuencia) en vez de intervalos de igual ancho,
    # porque Colima y Villa de Álvarez concentran casi toda la oferta y con igual
    # ancho 8 de 10 municipios caerían en la misma categoría.
    m["oferta_nivel"] = pd.qcut(m["consultorios_por_100k"].rank(method="first"), 3, labels=["baja", "media", "alta"])
    m["necesidad_nivel"] = pd.qcut(m["tasa_suicidio_anual_100k"].rank(method="first"), 3, labels=["baja", "media", "alta"])

    # Nombres DENUE vs Censo (conflicto de codificación/escritura)
    nombres_denue = den.groupby("cve_mun")["municipio"].first()
    difieren = [(k, v, m.set_index("cve_mun").loc[k, "nom_mun"]) for k, v in nombres_denue.items()
                if k in set(m["cve_mun"]) and v != m.set_index("cve_mun").loc[k, "nom_mun"]]
    rep(f"Nombres de municipio que difieren entre DENUE y Censo: **{len(difieren)}** "
        + (", ".join(f"{k}: '{a}' vs '{b}'" for k, a, b in difieren) if difieren else "(ninguno tras pasar todo a UTF-8)") + ".")
    rep()

    # Linaje: registros EDR + establecimientos DENUE + fila del Censo
    lin = [linaje("municipios_colima", s["mun_resid"], s),
           linaje("municipios_colima", psic["cve_mun"], psic)]
    censo_l = cen[cen["cve_mun"].isin(m["cve_mun"])]
    lin.append(linaje("municipios_colima", censo_l["cve_mun"], censo_l))
    todo = pd.concat(lin)
    rl = todo.groupby("clave_oro").agg(n_registros_fuente=("id_registro", "size"), fecha_ingesta_max=("fecha_ingesta_utc", "max"))
    m = m.drop(columns=["id_censo"]).join(rl, on="cve_mun")
    guardar(m, "municipios_colima.csv")
    return m, lin


# --------------------------------------------------------------------------- main
def main() -> None:
    d, den, cen = cargar()
    d = jerarquias(d)
    residentes = d[d["ent_resid"] == "06"].copy()
    rep("# Reporte de limpieza y preprocesamiento — E1")
    rep()
    rep("> Archivo generado automáticamente por `src/oro.py`. No editar a mano: las cifras se recalculan en cada corrida.")
    rep()
    rep(f"Alcance: defunciones de **residentes del estado de Colima** (`ent_resid = 06`). Se excluyen "
        f"{int((d['ent_resid'] != '06').sum()):,} registros de no residentes o con residencia desconocida "
        f"({int(d['ent_resid'].isna().sum())} desconocida); siguen en Plata, solo quedan fuera del análisis.")
    rep()
    diagnostico_faltantes(residentes)
    residentes = imputar(residentes)
    mensual, lin1 = series(residentes)
    lin2 = factores(residentes)
    mun, lin3 = municipios(residentes, den, cen)

    rep("## 4. Normalización y estandarización")
    rep()
    rep("Se calculan **Min-Max** (`x' = (x − min)/(max − min)`, rango [0, 1]) y **Z-Score** (`(x − media)/desv`) "
        "para las series mensual y trimestral y para las variables municipales. Min-Max se usará en el "
        "agrupamiento de municipios (E3), donde todas las variables deben pesar igual. Z-Score se usará en "
        "modelos que suponen variables centradas. Las columnas originales se conservan.")
    rep()
    rep("## 5. Discretización y jerarquías conceptuales")
    rep()
    rep("| Dimensión | Jerarquía |")
    rep("|---|---|")
    rep("| Causa | código CIE-10 (X700) → categoría (X70) → grupo analítico (suicidio X60–X84 / trastorno mental F / otra) → capítulo (X) |")
    rep("| Tiempo | día → mes → trimestre → semestre → año |")
    rep("| Lugar | municipio → zona (Zona Metropolitana Colima–Villa de Álvarez / resto) → estado |")
    rep(f"| Edad | años → grupo {', '.join(ETIQ_EDAD)}. Cortes elegidos para coincidir con los grupos que publica el Censo y poder calcular tasas |")
    rep("| Oferta y necesidad municipal | valor continuo → nivel baja/media/alta por **terciles** (igual frecuencia). Con intervalos de igual ancho, la concentración de consultorios en la capital dejaría casi todos los municipios en *baja* |")
    rep()
    rep("## 6. Reducción de datos")
    rep()
    rep("- **Selección de variables:** de 59–74 columnas de EDR se conservan 13 (más las de linaje).")
    rep("- **Selección de filas:** solo residentes de Colima, años 2018–2023 y causas de salud mental.")
    rep("- **Agregación:** registro individual → conteo mensual (72 periodos) → conteo trimestral (24 periodos).")
    rep("- **Muestreo:** no se aplica. Los datos ya son el universo de registros y son pocos; muestrear solo perdería información.")
    rep()
    rep("## 7. Resultado")
    rep()
    rep(f"- Serie mensual: {len(mensual)} periodos; suicidios por mes: mín {mensual['suicidio'].min()}, mediana {mensual['suicidio'].median():.0f}, máx {mensual['suicidio'].max()}.")
    rep(f"- Suicidios con mes imputado: {int(mensual['suicidio_mes_imputado'].sum())}; trastornos mentales con mes imputado: {int(mensual['trastorno_mental_mes_imputado'].sum())}.")
    rep()
    rep("**Advertencia de áreas pequeñas:** en municipios con poca población (Ixtlahuacán, Minatitlán) un solo caso "
        "cambia mucho la tasa por 100 mil. Para E3 se recomienda suavizar las tasas (p. ej. Bayes empírico) o "
        "agrupar esos municipios antes de compararlos.")
    rep()
    rep("Tabla municipal integrada:")
    rep()
    rep(tabla_md(mun[["cve_mun", "nom_mun", "pobtot", "consultorios_psic", "consultorios_por_100k",
                      "tasa_suicidio_anual_100k", "oferta_nivel", "necesidad_nivel", "zona"]]))
    rep()

    lin = pd.concat(lin1 + lin2 + lin3, ignore_index=True)
    guardar(lin, "linaje_oro.csv")
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n".join(lineas_reporte) + "\n", encoding="utf-8")
    print(f"Oro generado. Linaje: {len(lin)} filas. Reporte: {REPORTE.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
