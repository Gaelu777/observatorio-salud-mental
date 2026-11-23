"""E2 · Experimento factorial (ruta ingeniería) sobre el propio pipeline.

Pregunta: ¿qué configuración del paso Bronce -> serie mensual procesa más rápido
sin introducir errores?

Tarea medida (igual en todas las corridas): leer los 6 CSV de defunciones de la
capa Bronce, limpiar espacios, quedarse con residentes de Colima, escribir el
intermedio a disco y contar suicidios (CIE-10 X60-X84) por mes.
Todo corre contra la COPIA LOCAL de Bronce: no se hace ninguna petición a INEGI.

Diseños:
  1. Factorial 2^3 completo, 3 réplicas, orden aleatorio dentro de cada réplica,
     réplica = bloque (controla el calentamiento de disco/caché entre pasadas).
       A  motor de lectura       : c (pandas)        vs pyarrow
       B  columnas leídas        : todas (59)         vs solo las 5 necesarias
       C  formato del intermedio : CSV                vs Parquet
  2. Dos factores con 3 niveles en uno: B (2 niveles) x Formato (CSV, Parquet,
     Feather), 3 réplicas -> ANOVA de dos vías con interacción.
  3. Matrices 2^4 completa y 2^(4-1) fraccionada (D = ABC) con su tabla de alias.
  4. Corrida de confirmación de la combinación ganadora.

Respuestas: tiempo en segundos (perf_counter) y error (1 si la serie resultante
no es idéntica a la serie de referencia).

Uso:  python src/experimento_factorial.py
Salida: docs/E2/experimento/ (corridas, tablas ANOVA, gráficas, resumen.json)
"""
from __future__ import annotations

import itertools
import json
import tempfile
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.anova import anova_lm

from comun import BRONCE, RAIZ

SEMILLA = 20261123
REPLICAS = 3
CORRIDAS_CONFIRMACION = 5
ARCHIVOS = sorted((BRONCE / "inegi_defunciones").glob("defunciones_colima_registradas_*.csv"))
COLS_NECESARIAS = ["ent_resid", "mun_resid", "causa_def", "mes_ocurr", "anio_ocur"]
SALIDA = RAIZ / "docs" / "E2" / "experimento"

NIVELES = {
    "A_motor": ["c", "pyarrow"],
    "B_columnas": ["todas", "necesarias"],
    "C_formato": ["csv", "parquet"],
}


# --------------------------------------------------------------------------- tarea medida
def tarea(motor: str, columnas: str, formato: str, tmp: Path) -> pd.Series:
    """Bronce -> intermedio en disco -> serie mensual de suicidios."""
    usecols = COLS_NECESARIAS if columnas == "necesarias" else None
    partes = [pd.read_csv(f, dtype=str, engine=motor, usecols=usecols, keep_default_na=False)
              for f in ARCHIVOS]
    d = pd.concat(partes, ignore_index=True)
    for c in COLS_NECESARIAS:
        d[c] = d[c].str.strip()
    d = d[d["ent_resid"] == "06"]

    ruta = tmp / f"intermedio.{formato}"
    if formato == "csv":
        d.to_csv(ruta, index=False)
        d = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    elif formato == "parquet":
        d.to_parquet(ruta, index=False)
        d = pd.read_parquet(ruta)
    else:  # feather
        d.reset_index(drop=True).to_feather(ruta)
        d = pd.read_feather(ruta)

    cat = d["causa_def"].str[:3]
    s = d[cat.between("X60", "X84")]
    return s.groupby([s["anio_ocur"], s["mes_ocurr"]]).size().sort_index()


def medir(motor, columnas, formato, tmp, referencia) -> tuple[float, int]:
    t0 = time.perf_counter()
    serie = tarea(motor, columnas, formato, tmp)
    seg = time.perf_counter() - t0
    error = int(not serie.equals(referencia))
    return seg, error


# --------------------------------------------------------------------------- diseños
def matriz_2k(k: int) -> pd.DataFrame:
    """Matriz de un 2^k completo en orden estándar (Yates), niveles -1/+1."""
    filas = list(itertools.product([-1, 1], repeat=k))
    m = pd.DataFrame([f[::-1] for f in filas], columns=list("ABCDEFG"[:k]))
    return m


def correr_2k3(tmp: Path, referencia: pd.Series, rng) -> pd.DataFrame:
    tratamientos = list(itertools.product(*NIVELES.values()))
    filas = []
    orden = 0
    for rep in range(1, REPLICAS + 1):          # cada réplica es un bloque
        for i in rng.permutation(len(tratamientos)):  # aleatorización dentro del bloque
            a, b, c = tratamientos[i]
            seg, err = medir(a, b, c, tmp, referencia)
            orden += 1
            filas.append({"orden": orden, "bloque": rep, "A_motor": a, "B_columnas": b,
                          "C_formato": c, "tiempo_seg": round(seg, 4), "error": err})
    return pd.DataFrame(filas)


def correr_dos_factores(tmp: Path, referencia: pd.Series, rng) -> pd.DataFrame:
    """B (2 niveles) x Formato (3 niveles), motor fijo en "c": pyarrow resultó
    corromper los datos en el 2^3 (ver resumen), así que no es un nivel válido."""
    formatos = ["csv", "parquet", "feather"]
    tratamientos = list(itertools.product(NIVELES["B_columnas"], formatos))
    filas = []
    for rep in range(1, REPLICAS + 1):
        for i in rng.permutation(len(tratamientos)):
            b, f = tratamientos[i]
            seg, err = medir("c", b, f, tmp, referencia)
            filas.append({"bloque": rep, "B_columnas": b, "formato": f,
                          "tiempo_seg": round(seg, 4), "error": err})
    return pd.DataFrame(filas)


def tabla_alias() -> pd.DataFrame:
    """2^(4-1) con generador D = ABC -> relación de definición I = ABCD (resolución IV)."""
    efectos = ["A", "B", "C", "D", "AB", "AC", "AD", "BC", "BD", "CD",
               "ABC", "ABD", "ACD", "BCD", "ABCD"]

    def por_I(e):
        s = set(e) ^ set("ABCD")  # multiplicar por ABCD (letras al cuadrado = I)
        return "".join(sorted(s)) or "I"

    vistos, filas = set(), []
    for e in efectos:
        if e in vistos:
            continue
        a = por_I(e)
        vistos.update({e, a})
        filas.append({"efecto": e, "confundido_con": a})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- análisis
def anova(df: pd.DataFrame, formula: str) -> tuple[pd.DataFrame, object]:
    modelo = smf.ols(formula, data=df).fit()
    return anova_lm(modelo, typ=2), modelo


def supuestos(modelo, df: pd.DataFrame, grupos: list[str]) -> dict:
    res = modelo.resid
    sw = stats.shapiro(res)
    celdas = [g["tiempo_seg"].to_numpy() for _, g in df.groupby(grupos)]
    lev = stats.levene(*celdas, center="median")
    return {"shapiro_W": round(float(sw.statistic), 4), "shapiro_p": round(float(sw.pvalue), 4),
            "levene_p": round(float(lev.pvalue), 4)}


def grafica_interaccion(df, x, traza, archivo, titulo):
    fig, ax = plt.subplots(figsize=(6, 4))
    medias = df.groupby([x, traza])["tiempo_seg"].mean().unstack()
    for col in medias.columns:
        ax.plot(medias.index, medias[col], marker="o", label=f"{traza} = {col}")
    ax.set_xlabel(x)
    ax.set_ylabel("Tiempo medio (s)")
    ax.set_title(titulo)
    ax.legend()
    fig.tight_layout()
    fig.savefig(archivo, dpi=120)
    plt.close(fig)


def grafica_residuos(modelo, archivo):
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.5))
    stats.probplot(modelo.resid, plot=ax[0])
    ax[0].set_title("Q-Q de residuos")
    ax[1].scatter(modelo.fittedvalues, modelo.resid, s=15)
    ax[1].axhline(0, color="gray", lw=1)
    ax[1].set_xlabel("Ajustados")
    ax[1].set_ylabel("Residuos")
    ax[1].set_title("Residuos vs. ajustados")
    fig.tight_layout()
    fig.savefig(archivo, dpi=120)
    plt.close(fig)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEMILLA)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        referencia = tarea("c", "todas", "csv", tmp)   # configuración actual del pipeline
        tarea("pyarrow", "todas", "csv", tmp)          # calentamiento (no se mide)

        # 1. Factorial 2^3 con réplicas y bloques
        d3 = correr_2k3(tmp, referencia, rng)
        d3.to_csv(SALIDA / "corridas_2k3.csv", index=False)
        tab3, mod3 = anova(d3, "tiempo_seg ~ C(bloque) + A_motor * B_columnas * C_formato")
        tab3.to_csv(SALIDA / "anova_2k3.csv")
        sup3 = supuestos(mod3, d3, ["A_motor", "B_columnas", "C_formato"])
        grafica_interaccion(d3, "B_columnas", "A_motor", SALIDA / "interaccion_AB.png",
                            "Interacción motor × columnas (2³)")
        grafica_residuos(mod3, SALIDA / "residuos_2k3.png")
        medias3 = (d3.groupby(["A_motor", "B_columnas", "C_formato"])
                   .agg(mean=("tiempo_seg", "mean"), std=("tiempo_seg", "std"),
                        tasa_error=("error", "mean"))
                   .round(4).sort_values("mean"))
        medias3.to_csv(SALIDA / "medias_2k3.csv")

        # Efectos principales en escala -1/+1 (efecto = media(+) - media(-))
        efectos = {}
        for f, (bajo, alto) in NIVELES.items():
            efectos[f] = round(d3.loc[d3[f] == alto, "tiempo_seg"].mean()
                               - d3.loc[d3[f] == bajo, "tiempo_seg"].mean(), 4)

        # Robustez: el tiempo suele tener residuos sesgados; se repite el ANOVA en log(tiempo)
        d3["log_tiempo"] = np.log(d3["tiempo_seg"])
        mod3_log = smf.ols("log_tiempo ~ C(bloque) + A_motor * B_columnas * C_formato", data=d3).fit()
        tab3_log = anova_lm(mod3_log, typ=2)
        tab3_log.to_csv(SALIDA / "anova_2k3_log.csv")
        sw_log = stats.shapiro(mod3_log.resid)

        # 2. Dos factores, uno con 3 niveles
        d2 = correr_dos_factores(tmp, referencia, rng)
        d2.to_csv(SALIDA / "corridas_dos_factores.csv", index=False)
        tab2, mod2 = anova(d2, "tiempo_seg ~ C(bloque) + B_columnas * formato")
        tab2.to_csv(SALIDA / "anova_dos_factores.csv")
        sup2 = supuestos(mod2, d2, ["B_columnas", "formato"])
        grafica_interaccion(d2, "formato", "B_columnas", SALIDA / "interaccion_formato.png",
                            "Interacción columnas × formato (2 × 3)")

        # 3. Matrices 2^4 y 2^(4-1)
        m16 = matriz_2k(4)
        m16.to_csv(SALIDA / "matriz_2k4_completa.csv", index_label="corrida")
        m8 = matriz_2k(3)
        m8["D"] = m8["A"] * m8["B"] * m8["C"]
        m8.to_csv(SALIDA / "matriz_2k4-1_fraccionada.csv", index_label="corrida")
        tabla_alias().to_csv(SALIDA / "alias_2k4-1.csv", index=False)

        # 4. Confirmación de la combinación ganadora
        # Gana la más rápida SIN errores: una configuración rápida que corrompe datos no sirve.
        validas = medias3[medias3["tasa_error"] == 0]
        ganadora = validas.index[0]
        conf = [medir(*ganadora, tmp, referencia) for _ in range(CORRIDAS_CONFIRMACION)]
        t_conf = [c[0] for c in conf]
        actual = d3[(d3.A_motor == "c") & (d3.B_columnas == "todas") & (d3.C_formato == "csv")]

    resumen = {
        "semilla": SEMILLA,
        "replicas": REPLICAS,
        "corridas_2k3": len(d3),
        "errores_totales": int(d3["error"].sum() + d2["error"].sum() + sum(c[1] for c in conf)),
        "efectos_principales_seg": efectos,
        "supuestos_2k3": sup3,
        "supuestos_dos_factores": sup2,
        "ganadora": dict(zip(NIVELES.keys(), ganadora)),
        "media_predicha_ganadora_seg": float(validas.iloc[0]["mean"]),
        "tasa_error_por_motor": d3.groupby("A_motor")["error"].mean().to_dict(),
        "shapiro_p_log_2k3": round(float(sw_log.pvalue), 4),
        "confirmacion_media_seg": round(float(np.mean(t_conf)), 4),
        "confirmacion_de_seg": round(float(np.std(t_conf, ddof=1)), 4),
        "configuracion_actual_media_seg": round(float(actual["tiempo_seg"].mean()), 4),
        "mejora_pct_vs_actual": round(100 * (1 - np.mean(t_conf) / actual["tiempo_seg"].mean()), 1),
    }
    (SALIDA / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    print("\nANOVA 2^3:\n", tab3.round(4))
    print("\nANOVA dos factores:\n", tab2.round(4))
    print("\nANOVA 2^3 log:\n", tab3_log.round(4))
    print("\nMedias 2^3:\n", medias3)


if __name__ == "__main__":
    main()
