"""E3 · Análisis multivariado: perfiles de localidades de Colima.

Por qué localidades y no municipios: la propuesta de E0 planteaba los 10
municipios, pero con n = 10 y 5 o más variables la matriz de covarianzas casi
no tiene grados de libertad, y el MANOVA y la prueba de Mardia no tienen poder.
Por eso se baja un nivel de la jerarquía (municipio -> localidad) y se usan las
**65 localidades con 500 habitantes o más**. Debajo de ese tamaño, el INEGI
reserva datos con "*" y las proporciones son muy inestables.

Unidad: localidad del Censo 2020 (ITER), datos públicos y agregados.
Variables (8):
  pct_sin_afiliacion     % de la población sin afiliación a servicios de salud
  escolaridad_prom       grado promedio de escolaridad (años)
  pct_60ymas             % de la población de 60 años y más
  pct_condicion_mental   % con algún problema o condición mental
  pct_viv_internet       % de viviendas habitadas con internet
  pct_desocupacion       % de la PEA desocupada
  pct_hogares_jefa       % de hogares con persona de referencia mujer
  log_dist_psicologo     log(1 + km al consultorio de psicología más cercano, DENUE)

Grupos (definidos en E0/E2, jerarquía municipio -> zona):
  zona          metropolitana (Colima, V. de Álvarez, Comala, Coquimatlán,
                Cuauhtémoc) vs resto del estado
  oferta_nivel  tercil de consultorios de psicología por 100 mil hab. del municipio

Pasos: matriz y covarianzas -> normalidad multivariada (Mardia + Q-Q de
Mahalanobis) -> PCA estandarizado (sedimentación, cargas, biplot, nombres)
-> MANOVA (Wilks, Pillai, M de Box) vs. ANOVA separados.

Uso:  python src/multivariado.py
Salida: data/oro/localidades_colima.csv (incluye las coordenadas en CP1 y CP2 para el tablero)
        docs/E3/multivariado/ (gráficas, tablas, resumen.json)
"""
from __future__ import annotations

import json
import re

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandera.pandas as pa
from scipy import stats
from statsmodels.multivariate.manova import MANOVA

from comun import RAIZ
from plata import leer_bronce, puerta_calidad, quitar_ruido_texto, ultimos_archivos

ORO = RAIZ / "data" / "oro"
SALIDA = RAIZ / "docs" / "E3" / "multivariado"
CUARENTENA = RAIZ / "data" / "cuarentena" / "censo2020_localidades_cuarentena.csv"
POB_MIN = 500
ZM_COLIMA = {"002", "003", "004", "005", "010"}
CRS_METRICO = 6372

VARS = ["pct_sin_afiliacion", "escolaridad_prom", "pct_60ymas", "pct_condicion_mental",
        "pct_viv_internet", "pct_desocupacion", "pct_hogares_jefa", "log_dist_psicologo"]
ETIQ = {"pct_sin_afiliacion": "Sin afiliación a salud", "escolaridad_prom": "Escolaridad",
        "pct_60ymas": "60 años y más", "pct_condicion_mental": "Condición mental",
        "pct_viv_internet": "Internet en vivienda", "pct_desocupacion": "Desocupación",
        "pct_hogares_jefa": "Hogares con jefa", "log_dist_psicologo": "Distancia a psicólogo"}

# Nombres de negocio de los componentes: se asignaron leyendo las cargas
# (ver docs/E3/multivariado.md). El signo se fija para que el nombre siga siendo
# verdadero si la descomposición cambia de signo (ver orientar()).
NOMBRES_CP = {1: "Urbanización y acceso a psicólogos", 2: "Vulnerabilidad del hogar"}


# --------------------------------------------------------------------------- datos
def gms_a_decimal(txt: str) -> float:
    """Convierte la coordenada del ITER (18°56'13.462" N) a grados decimales."""
    m = re.match(r"\s*(\d+)\D+(\d+)'([\d.]+)\"\s*([NSEW])", txt)
    if not m:
        return np.nan
    g, mi, s, h = m.groups()
    v = int(g) + int(mi) / 60 + float(s) / 3600
    return -v if h in "SW" else v


ESQUEMA_LOC = pa.DataFrameSchema(
    {
        "cve_mun": pa.Column(str, pa.Check.str_matches(r"^0(0[1-9]|10)$")),
        "pobtot": pa.Column(int, pa.Check.ge(POB_MIN)),
        **{v: pa.Column(float, pa.Check.in_range(0, 100)) for v in VARS if v.startswith("pct_")},
        "escolaridad_prom": pa.Column(float, pa.Check.in_range(0, 24)),
        "latitud": pa.Column(float, pa.Check.in_range(18.6, 19.6)),
        "longitud": pa.Column(float, pa.Check.in_range(-104.8, -103.4)),
    },
    unique=["cve_mun", "cve_loc"],
    strict=False,
)


def construir() -> pd.DataFrame:
    e = ultimos_archivos("INEGI-CENSO2020-ITER")[-1]
    df, _ = quitar_ruido_texto(leer_bronce(e, "CENSO", encoding="utf-8-sig"))
    df = df[(df["MUN"] != "000") & (~df["LOC"].isin(["0000", "9998", "9999"]))].copy()
    num = lambda c: pd.to_numeric(df[c].replace({"*": np.nan, "N/D": np.nan}), errors="coerce")  # noqa: E731
    df["pobtot"] = num("POBTOT")
    df = df[df["pobtot"] >= POB_MIN].copy()
    num = lambda c: pd.to_numeric(df[c].replace({"*": np.nan, "N/D": np.nan}), errors="coerce")  # noqa: E731
    out = pd.DataFrame({
        "id_registro": df["id_registro"], "archivo_bronce": df["archivo_bronce"], "fila_bronce": df["fila_bronce"],
        "cve_mun": df["MUN"], "nom_mun": df["NOM_MUN"], "cve_loc": df["LOC"], "nom_loc": df["NOM_LOC"],
        "pobtot": df["pobtot"].astype(int),
        "pct_sin_afiliacion": num("PSINDER") / df["pobtot"] * 100,
        "escolaridad_prom": num("GRAPROES"),
        "pct_60ymas": num("P_60YMAS") / df["pobtot"] * 100,
        "pct_condicion_mental": num("PCLIM_PMEN") / df["pobtot"] * 100,
        "pct_viv_internet": num("VPH_INTER") / num("TVIVPARHAB") * 100,
        "pct_desocupacion": num("PDESOCUP") / num("PEA") * 100,
        "pct_hogares_jefa": num("HOGJEF_F") / num("TOTHOG") * 100,
        "latitud": df["LATITUD"].map(gms_a_decimal), "longitud": df["LONGITUD"].map(gms_a_decimal),
        "fecha_ingesta_utc": df["fecha_ingesta_utc"],
    })
    validos, cuarentena = puerta_calidad(out, ESQUEMA_LOC, "censo_localidades")
    cuarentena.to_csv(CUARENTENA, index=False, encoding="utf-8", lineterminator="\n")

    # Distancia a la oferta: consultorio de psicología (DENUE, capa Oro) más cercano
    cons = pd.read_csv(ORO / "consultorios_psicologia_geo.csv")
    g_loc = gpd.GeoDataFrame(validos, geometry=gpd.points_from_xy(validos.longitud, validos.latitud),
                             crs=4326).to_crs(CRS_METRICO)
    g_con = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cons.longitud, cons.latitud), crs=4326).to_crs(CRS_METRICO)
    cerca = gpd.sjoin_nearest(g_loc, g_con, distance_col="dist_m")
    cerca = cerca[~cerca.index.duplicated()]  # empates: un solo vecino por localidad
    validos = validos.assign(dist_psicologo_km=(cerca["dist_m"] / 1000).round(3).values)
    validos["log_dist_psicologo"] = np.log1p(validos["dist_psicologo_km"])

    mun = pd.read_csv(ORO / "municipios_colima.csv", dtype={"cve_mun": str})
    validos["zona"] = np.where(validos["cve_mun"].isin(ZM_COLIMA), "metropolitana", "resto")
    validos = validos.merge(mun[["cve_mun", "oferta_nivel"]], on="cve_mun", how="left")
    for c in VARS + ["dist_psicologo_km"]:
        validos[c] = validos[c].round(4)
    return validos.reset_index(drop=True)


# --------------------------------------------------------------------------- pruebas
def mardia(x: np.ndarray) -> dict:
    """Prueba de Mardia de asimetría y curtosis multivariada (Mardia, 1970)."""
    n, p = x.shape
    c = x - x.mean(0)
    s = np.cov(c, rowvar=False, bias=True)  # estimador de máxima verosimilitud (divide entre n)
    d = c @ np.linalg.inv(s) @ c.T
    b1 = (d ** 3).sum() / n ** 2
    b2 = (np.diag(d) ** 2).mean()
    chi_asim = n * b1 / 6
    gl = p * (p + 1) * (p + 2) / 6
    z_curt = (b2 - p * (p + 2)) / np.sqrt(8 * p * (p + 2) / n)
    return {"asimetria_b1p": round(b1, 3), "asimetria_chi2": round(chi_asim, 2), "gl": int(gl),
            "asimetria_p": float(stats.chi2.sf(chi_asim, gl)),
            "curtosis_b2p": round(b2, 3), "curtosis_esperada": p * (p + 2), "curtosis_z": round(z_curt, 3),
            "curtosis_p": float(2 * stats.norm.sf(abs(z_curt)))}


def box_m(x: np.ndarray, g: np.ndarray) -> dict:
    """M de Box: igualdad de matrices de covarianzas entre grupos (supuesto del MANOVA)."""
    niveles = np.unique(g)
    n, p, k = len(x), x.shape[1], len(niveles)
    sp, suma, inv = np.zeros((p, p)), 0.0, 0.0
    for lv in niveles:
        xi = x[g == lv]
        si = np.cov(xi, rowvar=False)
        sp += (len(xi) - 1) * si
        suma += (len(xi) - 1) * np.linalg.slogdet(si)[1]
        inv += 1 / (len(xi) - 1)
    sp /= n - k
    m = (n - k) * np.linalg.slogdet(sp)[1] - suma
    c = (2 * p ** 2 + 3 * p - 1) / (6 * (p + 1) * (k - 1)) * (inv - 1 / (n - k))
    gl = p * (p + 1) * (k - 1) / 2
    return {"M": round(m, 2), "chi2": round(m * (1 - c), 2), "gl": int(gl),
            "p": float(stats.chi2.sf(m * (1 - c), gl))}


def pillai(x: np.ndarray, g: np.ndarray) -> float:
    """Traza de Pillai: tr(H (H + E)^-1), con H entre grupos y E dentro de grupos."""
    c = x - x.mean(0)
    t = c.T @ c
    e = np.zeros_like(t)
    for lv in np.unique(g):
        ci = x[g == lv] - x[g == lv].mean(0)
        e += ci.T @ ci
    return float(np.trace((t - e) @ np.linalg.inv(t)))


def permutacion_pillai(x: np.ndarray, g: np.ndarray, n_perm: int = 4999, semilla: int = 20261130) -> dict:
    """MANOVA por permutación: revuelve las etiquetas de grupo y cuenta cuántas veces
    sale un Pillai >= al observado. No supone normalidad ni covarianzas iguales."""
    rng = np.random.default_rng(semilla)
    obs = pillai(x, g)
    mayores = sum(pillai(x, rng.permutation(g)) >= obs for _ in range(n_perm))
    return {"pillai_observado": round(obs, 4), "permutaciones": n_perm, "p": (mayores + 1) / (n_perm + 1)}


def manova(df: pd.DataFrame, grupo: str) -> dict:
    formula = " + ".join(VARS) + f" ~ C({grupo})"
    res = MANOVA.from_formula(formula, data=df).mv_test().results[f"C({grupo})"]["stat"]
    out = {}
    for nombre, clave in [("Wilks' lambda", "wilks"), ("Pillai's trace", "pillai"),
                          ("Hotelling-Lawley trace", "hotelling"), ("Roy's greatest root", "roy")]:
        r = res.loc[nombre]
        out[clave] = {"valor": round(float(r["Value"]), 4), "F": round(float(r["F Value"]), 3),
                      "gl_num": float(r["Num DF"]), "gl_den": float(r["Den DF"]), "p": float(r["Pr > F"])}
    # ANOVA de un factor por variable, para contrastar con el MANOVA
    anovas = {}
    for v in VARS:
        grupos = [s.values for _, s in df.groupby(grupo)[v]]
        f, pv = stats.f_oneway(*grupos)
        anovas[v] = {"F": round(float(f), 3), "p": float(pv), "p_bonferroni": float(min(1, pv * len(VARS)))}
    medias = df.groupby(grupo)[VARS].mean().round(3)
    tam = df[grupo].value_counts().to_dict()
    return {"n_por_grupo": {str(k): int(v) for k, v in tam.items()}, "estadisticos": out, "anovas": anovas,
            "medias": medias.to_dict("index"),
            "box_m": box_m(df[VARS].to_numpy(float), df[grupo].to_numpy()),
            "permutacion": permutacion_pillai(df[VARS].to_numpy(float), df[grupo].to_numpy())}


# --------------------------------------------------------------------------- PCA
def orientar(vec: np.ndarray, ref: int) -> np.ndarray:
    """Fija el signo del componente para que la variable de referencia cargue positivo."""
    return vec if vec[ref] >= 0 else -vec


def pca(z: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r = np.corrcoef(z, rowvar=False)
    val, vec = np.linalg.eigh(r)
    orden = np.argsort(val)[::-1]
    val, vec = val[orden], vec[:, orden]
    # CP1 orientado a escolaridad (+); CP2 orientado a 60 y más (+)
    vec[:, 0] = orientar(vec[:, 0], VARS.index("escolaridad_prom"))
    vec[:, 1] = orientar(vec[:, 1], VARS.index("pct_60ymas"))
    return val, vec, z @ vec


# --------------------------------------------------------------------------- gráficas
def graficas(df: pd.DataFrame, z: np.ndarray, val, vec, puntajes, d2) -> None:
    n, p = z.shape
    # Matriz de correlaciones
    r = np.corrcoef(df[VARS].to_numpy(float), rowvar=False)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(r, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(p), [ETIQ[v] for v in VARS], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(p), [ETIQ[v] for v in VARS], fontsize=8)
    for i in range(p):
        for j in range(p):
            ax.text(j, i, f"{r[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(r[i, j]) > 0.6 else "black")
    fig.colorbar(im, shrink=0.8)
    ax.set_title("Matriz de correlaciones (65 localidades)")
    fig.tight_layout()
    fig.savefig(SALIDA / "01_correlaciones.png", dpi=120)
    plt.close(fig)

    # Q-Q de distancias de Mahalanobis vs chi-cuadrada(p)
    q = stats.chi2.ppf((np.arange(1, n + 1) - 0.5) / n, p)
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.scatter(q, np.sort(d2), s=14)
    lim = max(q.max(), d2.max()) * 1.05
    ax.plot([0, lim], [0, lim], "r--", lw=1)
    corte = stats.chi2.ppf(0.975, p)
    ax.axhline(corte, color="gray", ls=":", lw=1)
    ax.text(0.5, corte * 1.02, "χ² 97.5 %", fontsize=7, color="gray")
    ax.set(xlabel=f"Cuantiles teóricos χ²({p})", ylabel="Distancia de Mahalanobis² ordenada",
           title="Q-Q de Mahalanobis")
    fig.tight_layout()
    fig.savefig(SALIDA / "02_qq_mahalanobis.png", dpi=120)
    plt.close(fig)

    # Sedimentación
    prop = val / val.sum()
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.plot(range(1, p + 1), val, "o-", label="valor propio")
    ax.axhline(1, color="gray", ls="--", lw=1, label="criterio de Kaiser (λ = 1)")
    for i, (v, pr) in enumerate(zip(val, np.cumsum(prop), strict=True)):
        ax.text(i + 1.1, v + 0.05, f"{pr:.0%}", fontsize=7)
    ax.set(xlabel="Componente", ylabel="Valor propio", title="Gráfica de sedimentación (% acumulado)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(SALIDA / "03_sedimentacion.png", dpi=120)
    plt.close(fig)

    # Biplot
    fig, ax = plt.subplots(figsize=(9.5, 7.5))
    colores = {"metropolitana": "#1f77b4", "resto": "#d95f02"}
    for zona, sub in df.groupby("zona"):
        idx = sub.index.to_numpy()
        ax.scatter(puntajes[idx, 0], puntajes[idx, 1], s=np.sqrt(sub["pobtot"]) / 2.5 + 8,
                   alpha=0.65, c=colores[zona], label=f"Zona {zona} ({len(sub)})", edgecolors="white", lw=0.5)
    destacar = set(df.nlargest(6, "pobtot").index) | set(np.argsort(puntajes[:, 0])[:3]) \
        | set(np.argsort(puntajes[:, 1])[-3:]) | set(np.argsort(puntajes[:, 1])[:2])
    for i in destacar:
        ax.annotate(df.loc[i, "nom_loc"][:22], (puntajes[i, 0], puntajes[i, 1]), fontsize=7,
                    xytext=(3, 3), textcoords="offset points")
    esc = np.abs(puntajes[:, :2]).max() * 0.85
    for k, v in enumerate(VARS):
        ax.arrow(0, 0, vec[k, 0] * esc, vec[k, 1] * esc, color="#444", width=0.01, head_width=0.08, alpha=0.8)
        ax.text(vec[k, 0] * esc * 1.12, vec[k, 1] * esc * 1.12, ETIQ[v], fontsize=8, color="#222",
                ha="center", weight="bold")
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    ax.set(xlabel=f"CP1 · {NOMBRES_CP[1]} ({prop[0]:.0%})", ylabel=f"CP2 · {NOMBRES_CP[2]} ({prop[1]:.0%})",
           title="Biplot: localidades de Colima en los dos primeros componentes")
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(SALIDA / "04_biplot.png", dpi=130)
    plt.close(fig)

    # Mapa geográfico del CP1
    mun = gpd.read_file(RAIZ / "data" / "bronce" / "inegi_marcogeo2020" / "06mun.shp").to_crs(4326)
    fig, ax = plt.subplots(figsize=(8, 7))
    mun.plot(ax=ax, color="#f2f2f2", edgecolor="#999", lw=0.7)
    sc = ax.scatter(df["longitud"], df["latitud"], c=puntajes[:, 0], cmap="viridis",
                    s=np.sqrt(df["pobtot"]) / 2 + 10, edgecolors="k", lw=0.3)
    fig.colorbar(sc, ax=ax, shrink=0.7, label=f"CP1 · {NOMBRES_CP[1]}")
    ax.set_title("Localidades por urbanización y acceso a psicólogos (CP1; bajo = menos acceso)")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(SALIDA / "05_mapa_cp1.png", dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- main
def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    df = construir()
    x = df[VARS].to_numpy(float)
    n, p = x.shape

    res: dict = {"unidad": f"localidad del Censo 2020 con >= {POB_MIN} habitantes", "n": n, "p": p,
                 "variables": VARS}
    # Vector de medias, covarianzas y correlaciones
    pd.DataFrame(np.cov(x, rowvar=False), index=VARS, columns=VARS).round(4).to_csv(SALIDA / "covarianzas.csv")
    pd.DataFrame(np.corrcoef(x, rowvar=False), index=VARS, columns=VARS).round(3).to_csv(SALIDA / "correlaciones.csv")
    res["descriptivos"] = df[VARS + ["dist_psicologo_km"]].describe().round(3).to_dict()

    # Normalidad multivariada
    c = x - x.mean(0)
    d2 = np.einsum("ij,jk,ik->i", c, np.linalg.inv(np.cov(x, rowvar=False)), c)
    corte = stats.chi2.ppf(0.975, p)
    res["normalidad"] = {"mardia": mardia(x),
                         "mahalanobis_sobre_chi2_975": df.loc[d2 > corte, "nom_loc"].tolist(),
                         "shapiro_por_variable_p": {v: round(float(stats.shapiro(df[v]).pvalue), 4) for v in VARS}}
    df["mahalanobis2"] = d2.round(3)

    # PCA sobre datos estandarizados
    z = (x - x.mean(0)) / x.std(0, ddof=1)
    val, vec, puntajes = pca(z)
    prop = val / val.sum()
    cargas = pd.DataFrame(vec[:, :4] * np.sqrt(val[:4]), index=VARS,
                          columns=[f"CP{i}" for i in range(1, 5)]).round(3)  # correlación variable-componente
    cargas.to_csv(SALIDA / "cargas.csv")
    res["pca"] = {"valores_propios": [round(float(v), 3) for v in val],
                  "varianza_explicada": [round(float(v), 4) for v in prop],
                  "varianza_acumulada": [round(float(v), 4) for v in np.cumsum(prop)],
                  "kaiser_retiene": int((val > 1).sum()), "nombres": NOMBRES_CP,
                  "cargas": cargas.to_dict()}
    df["cp1"], df["cp2"] = puntajes[:, 0].round(4), puntajes[:, 1].round(4)
    res["extremos_cp1"] = {"bajo": df.nsmallest(5, "cp1")[["nom_loc", "nom_mun", "cp1"]].to_dict("records"),
                           "alto": df.nlargest(5, "cp1")[["nom_loc", "nom_mun", "cp1"]].to_dict("records")}
    res["extremos_cp2"] = {"alto": df.nlargest(5, "cp2")[["nom_loc", "nom_mun", "cp2"]].to_dict("records")}

    # MANOVA
    res["manova_zona"] = manova(df, "zona")
    res["manova_oferta"] = manova(df, "oferta_nivel")

    graficas(df, z, val, vec, puntajes, d2)

    cols = ["id_registro", "archivo_bronce", "fila_bronce", "cve_mun", "nom_mun", "cve_loc", "nom_loc", "pobtot",
            *VARS[:-1], "dist_psicologo_km", "log_dist_psicologo", "zona", "oferta_nivel", "latitud", "longitud",
            "mahalanobis2", "cp1", "cp2", "fecha_ingesta_utc"]
    df[cols].to_csv(ORO / "localidades_colima.csv", index=False, encoding="utf-8", lineterminator="\n")
    (SALIDA / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ["n", "normalidad", "pca", "extremos_cp1", "extremos_cp2"]},
                     ensure_ascii=False, indent=1, default=str))
    for g in ["manova_zona", "manova_oferta"]:
        print(g, json.dumps({k: res[g][k] for k in ["n_por_grupo", "box_m", "permutacion"]}, default=str))
        print({v: round(a["p"], 4) for v, a in res[g]["anovas"].items()})
        print(res[g]["medias"])


if __name__ == "__main__":
    main()
