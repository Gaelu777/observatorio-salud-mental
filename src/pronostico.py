"""E1 · Laboratorio de series de tiempo: pronóstico mensual de suicidios en Colima.

Variable (pregunta analítica E1 de la propuesta): defunciones por lesiones
autoinfligidas (CIE-10 X60-X84) de residentes de Colima, por mes de ocurrencia.
Entrada: data/oro/serie_mensual_colima.csv (72 meses, ene-2018 a dic-2023).

Pasos (en el orden de la rúbrica E1 de Análisis Estadístico):
  1. Caracterización: gráfica, media móvil (tendencia), perfil mensual
     (estacionalidad) y prueba de cambio estructural (medias 2018-20 vs 2021-23).
  2. Descomposición ADITIVA (la multiplicativa no aplica: la serie tiene meses en 0
     y la amplitud estacional no crece con el nivel).
  3. Estacionariedad: Dickey-Fuller aumentada (y KPSS como contraste);
     diferenciación solo si hace falta.
  4. ACF y PACF; correlación cruzada con la 2a variable del observatorio
     (defunciones por trastornos mentales y del comportamiento, F00-F99).
  5. Cuatro modelos: suavizamiento simple, Holt, Holt-Winters y ARIMA.
     (p, d, q) por ADF + ACF/PACF + rejilla de AIC.
  6. Selección con datos que el modelo no vio: últimos 12 meses (2023) como prueba,
     MAE, RMSE y MAPE. Gana el menor error, no el más sofisticado.
  7. Residuos del ganador: Ljung-Box y varianza estable (Levene entre mitades).
  8. Pronóstico de 12 meses (2024) con intervalo de predicción del 95 %.

Uso:  python src/pronostico.py
Salida: docs/E1/pronostico/ (gráficas, tablas, resumen.json)
        data/oro/pronostico_suicidio_colima.csv (lo lee el tablero)
"""
from __future__ import annotations

import itertools
import json
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, adfuller, ccf, kpss, pacf

from comun import RAIZ

warnings.filterwarnings("ignore")  # avisos de convergencia de statsmodels en la rejilla

ENTRADA = RAIZ / "data" / "oro" / "serie_mensual_colima.csv"
SALIDA = RAIZ / "docs" / "E1" / "pronostico"
SALIDA_ORO = RAIZ / "data" / "oro" / "pronostico_suicidio_colima.csv"
H_PRUEBA = 12      # meses reservados como prueba (todo 2023)
H_FUTURO = 12      # meses a pronosticar (2024)
ALFA = 0.05        # intervalo de predicción del 95 %


def cargar() -> pd.DataFrame:
    s = pd.read_csv(ENTRADA)
    s.index = pd.PeriodIndex(s["periodo"], freq="M").to_timestamp()
    s.index.freq = "MS"
    return s


# ---------------------------------------------------------------- 1-4 · caracterización
def caracterizar(s: pd.DataFrame, res: dict) -> None:
    y = s["suicidio"].astype(float)
    tm = s["trastorno_mental"].astype(float)

    # 1. Serie, tendencia (media móvil centrada de 12) y cambio estructural
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(y.index, y, marker="o", ms=3, lw=1, label="Suicidios por mes")
    ax.plot(y.index, y.rolling(12, center=True).mean(), lw=2.5, label="Media móvil 12 meses")
    for a in range(2018, 2024):
        m = y[str(a)].mean()
        ax.hlines(m, pd.Timestamp(f"{a}-01-01"), pd.Timestamp(f"{a}-12-01"), colors="gray", ls=":")
    ax.set(title="Suicidios mensuales de residentes de Colima (INEGI EDR)", ylabel="defunciones")
    ax.legend()
    fig.tight_layout()
    fig.savefig(SALIDA / "01_serie.png", dpi=120)
    plt.close(fig)

    a, b = y[:"2020"], y["2021":]
    t = stats.mannwhitneyu(a, b)
    res["caracterizacion"] = {
        "n": int(len(y)), "media": round(y.mean(), 2), "desv": round(y.std(), 2),
        "min": int(y.min()), "max": int(y.max()),
        "max_periodo": str(y.idxmax().date())[:7],
        "media_por_anio": {str(k): round(v, 2) for k, v in y.groupby(y.index.year).mean().items()},
        "cambio_estructural": {
            "media_2018_2020": round(a.mean(), 2), "media_2021_2023": round(b.mean(), 2),
            "mann_whitney_p": round(float(t.pvalue), 4),
        },
    }

    # Perfil mensual (estacionalidad a simple vista)
    perfil = y.groupby(y.index.month).agg(["mean", "std"])
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(perfil.index, perfil["mean"], yerr=perfil["std"], capsize=3, color="#4c72b0")
    ax.set(xticks=range(1, 13), title="Promedio por mes del año (2018-2023), barra = ±1 desv.",
           xlabel="mes", ylabel="suicidios promedio")
    fig.tight_layout()
    fig.savefig(SALIDA / "02_perfil_mensual.png", dpi=120)
    plt.close(fig)
    kw = stats.kruskal(*[g.values for _, g in y.groupby(y.index.month)])
    res["caracterizacion"]["perfil_mensual"] = {int(k): round(v, 2) for k, v in perfil["mean"].items()}
    res["caracterizacion"]["kruskal_mes_p"] = round(float(kw.pvalue), 4)

    # 2. Descomposición aditiva
    d = seasonal_decompose(y, model="additive", period=12)
    fig = d.plot()
    fig.set_size_inches(10, 7)
    fig.suptitle("Descomposición aditiva (periodo 12)", y=1.0)
    fig.tight_layout()
    fig.savefig(SALIDA / "03_descomposicion.png", dpi=120)
    plt.close(fig)
    var_res = np.nanvar(d.resid)
    res["descomposicion"] = {
        "modelo": "aditivo",
        "amplitud_estacional": round(float(d.seasonal.max() - d.seasonal.min()), 2),
        # Fuerza de la estacionalidad (Hyndman): 1 - Var(R)/Var(S+R), 0 = nada, 1 = fuerte
        "fuerza_estacional": round(float(max(0, 1 - var_res / np.nanvar(d.seasonal + d.resid))), 3),
        "fuerza_tendencia": round(float(max(0, 1 - var_res / np.nanvar(d.trend + d.resid))), 3),
        "indices_estacionales": {int(k): round(float(v), 2)
                                 for k, v in d.seasonal[:12].groupby(d.seasonal[:12].index.month).first().items()},
    }

    # 3. Estacionariedad
    adf = adfuller(y, autolag="AIC")
    kp = kpss(y, regression="c", nlags="auto")
    adf_d = adfuller(y.diff().dropna(), autolag="AIC")
    res["estacionariedad"] = {
        "adf_estadistico": round(adf[0], 3), "adf_p": round(adf[1], 4), "adf_rezagos": int(adf[2]),
        "kpss_estadistico": round(kp[0], 3), "kpss_p": round(kp[1], 4),
        "adf_primera_diferencia_p": round(adf_d[1], 6),
        "d_elegido": 0 if adf[1] < 0.05 else 1,
    }

    # 4. ACF / PACF y correlación cruzada
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.5))
    plot_acf(y, lags=24, ax=axs[0], title="ACF suicidios")
    plot_pacf(y, lags=24, ax=axs[1], title="PACF suicidios", method="ywm")
    fig.tight_layout()
    fig.savefig(SALIDA / "04_acf_pacf.png", dpi=120)
    plt.close(fig)
    banda = 1.96 / np.sqrt(len(y))
    va, vp = acf(y, nlags=24), pacf(y, nlags=24, method="ywm")
    res["autocorrelacion"] = {
        "banda_95": round(banda, 3),
        "acf_1_a_3": [round(v, 3) for v in va[1:4]], "acf_12": round(va[12], 3),
        "pacf_1_a_3": [round(v, 3) for v in vp[1:4]], "pacf_12": round(vp[12], 3),
        "rezagos_acf_significativos": [k for k in range(1, 25) if abs(va[k]) > banda],
        "rezagos_pacf_significativos": [k for k in range(1, 25) if abs(vp[k]) > banda],
        "ljung_box_serie_original_p_lag12": round(float(acorr_ljungbox(y, lags=[12])["lb_pvalue"].iloc[0]), 4),
    }

    # Correlación cruzada: corr(suicidio_t, trastorno_{t-k}), k = 0..6
    cc = ccf(y - y.mean(), tm - tm.mean(), adjusted=False, nlags=7)
    # ccf(x, y)[k] = corr(x_{t+k}, y_t) -> trastorno k meses ANTES que suicidio
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.stem(range(len(cc)), cc)
    ax.axhline(banda, ls="--", c="gray")
    ax.axhline(-banda, ls="--", c="gray")
    ax.set(title="Correlación cruzada: suicidio(t) vs trastorno mental(t−k)", xlabel="k (meses)")
    fig.tight_layout()
    fig.savefig(SALIDA / "05_correlacion_cruzada.png", dpi=120)
    plt.close(fig)
    r0, p0 = stats.pearsonr(y, tm)
    res["correlacion_cruzada"] = {
        "segunda_variable": "trastorno_mental (CIE-10 F00-F99)",
        "ccf_k0_a_k6": [round(v, 3) for v in cc[:7]],
        "pearson_k0": round(r0, 3), "pearson_k0_p": round(p0, 4),
        "spearman_k0": round(stats.spearmanr(y, tm)[0], 3),
    }


# ---------------------------------------------------------------- 5-6 · modelos
def ajustar(nombre: str, y: pd.Series, orden: tuple | None = None):
    if nombre == "SES":
        return ETSModel(y, error="add", trend=None, seasonal=None).fit(disp=False)
    if nombre == "Holt":
        return ETSModel(y, error="add", trend="add", damped_trend=False).fit(disp=False)
    if nombre == "Holt-Winters":
        return ETSModel(y, error="add", trend="add", seasonal="add", seasonal_periods=12,
                        damped_trend=True).fit(disp=False)
    if nombre.startswith("ARIMA"):
        return ARIMA(y, order=orden).fit()
    raise ValueError(nombre)


def pronosticar(modelo, h: int, inicio: pd.Timestamp) -> pd.DataFrame:
    if isinstance(modelo.model, ETSModel):
        p = modelo.get_prediction(start=len(modelo.data.endog), end=len(modelo.data.endog) + h - 1)
        f = p.summary_frame(alpha=ALFA)
        out = pd.DataFrame({"media": f["mean"], "inf": f["pi_lower"], "sup": f["pi_upper"]})
    else:
        p = modelo.get_forecast(h)
        ci = p.conf_int(alpha=ALFA)
        out = pd.DataFrame({"media": p.predicted_mean, "inf": ci.iloc[:, 0], "sup": ci.iloc[:, 1]})
    out.index = pd.date_range(inicio, periods=h, freq="MS")
    return out


def metricas(real: pd.Series, pred: pd.Series) -> dict:
    e = real.values - pred.values
    return {"MAE": round(float(np.mean(np.abs(e))), 3),
            "RMSE": round(float(np.sqrt(np.mean(e ** 2))), 3),
            # MAPE es válido aquí: 2023 no tiene ningún mes en cero
            "MAPE_%": round(float(np.mean(np.abs(e / real.values)) * 100), 1)}


def elegir_arima(y: pd.Series, d: int) -> tuple[tuple, pd.DataFrame]:
    filas = []
    for p, q in itertools.product(range(4), range(4)):
        try:
            m = ARIMA(y, order=(p, d, q)).fit()
            filas.append({"p": p, "d": d, "q": q, "AIC": round(m.aic, 2), "BIC": round(m.bic, 2)})
        except Exception:  # noqa: BLE001 - combinaciones que no convergen se omiten
            pass
    t = pd.DataFrame(filas).sort_values("AIC").reset_index(drop=True)
    mejor = t.iloc[0]
    return (int(mejor.p), int(mejor.d), int(mejor.q)), t


def modelar(s: pd.DataFrame, res: dict) -> None:
    y = s["suicidio"].astype(float)
    ent, prueba = y[:-H_PRUEBA], y[-H_PRUEBA:]
    d = res["estacionariedad"]["d_elegido"]

    orden, rejilla = elegir_arima(ent, d)
    rejilla.to_csv(SALIDA / "arima_rejilla_aic.csv", index=False)

    # Candidato extra: AR solo con los rezagos que la PACF marcó significativos (<= 12).
    # Sirve para comprobar si la estructura que "se ve" en la PACF mejora el pronóstico
    # o es ruido de muestreo (con 72 datos, 1 de cada 20 rezagos sale por azar).
    rez = [k for k in res["autocorrelacion"]["rezagos_pacf_significativos"] if k <= 12]
    orden_pacf = (rez, d, 0)
    ordenes = {"ARIMA": orden, "ARIMA-PACF": orden_pacf}
    etiquetas = {"ARIMA": f"ARIMA{orden}", "ARIMA-PACF": f"ARIMA(p={rez},{d},0)"}

    filas, preds, modelos = [], {}, {}
    for nombre in ["SES", "Holt", "Holt-Winters", "ARIMA", "ARIMA-PACF"]:
        m = ajustar(nombre, ent, ordenes.get(nombre))
        f = pronosticar(m, H_PRUEBA, prueba.index[0])
        preds[nombre], modelos[nombre] = f, m
        filas.append({"modelo": etiquetas.get(nombre, nombre), "clave": nombre,
                      "AIC_entrenamiento": round(m.aic, 2), **metricas(prueba, f["media"])})
    # Referencia ingenua (pronóstico = media del entrenamiento): un modelo que no la
    # supera no aporta nada.
    ing = pd.Series(ent.mean(), index=prueba.index)
    filas.append({"modelo": "Referencia: media histórica", "clave": "referencia", "AIC_entrenamiento": np.nan,
                  **metricas(prueba, ing)})
    tabla = pd.DataFrame(filas)
    tabla.to_csv(SALIDA / "comparacion_modelos.csv", index=False)

    cand = tabla[tabla["clave"] != "referencia"]
    ganador_fila = cand.sort_values(["RMSE", "MAE"]).iloc[0]
    ganador = ganador_fila["clave"]

    # Parámetros ajustados, para justificarlos en el reporte
    params = {}
    for n, m in modelos.items():
        params[n] = {k: round(float(v), 4) for k, v in zip(m.param_names, m.params, strict=False)
                     if not k.startswith("initial_")}

    # Gráfica de los 4 modelos sobre la prueba
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(y["2021":].index, y["2021":], "k-o", ms=3, lw=1, label="Real")
    for n, f in preds.items():
        ax.plot(f.index, f["media"], lw=2, label=n + (" ◀ ganador" if n == ganador else ""))
    ax.axvspan(prueba.index[0], prueba.index[-1], color="gray", alpha=0.12)
    ax.set(title="Prueba fuera de muestra (2023): los modelos vs. lo que pasó", ylabel="suicidios")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(SALIDA / "06_modelos_prueba.png", dpi=120)
    plt.close(fig)

    res["arima"] = {"orden_por_AIC": list(orden), "orden_por_PACF": [rez, d, 0],
                    "top5_rejilla": rejilla.head(5).to_dict("records")}
    res["parametros"] = params
    res["comparacion"] = tabla.to_dict("records")
    res["ganador"] = ganador_fila["modelo"]

    # ------------------------------------------------------------ 7 · residuos
    final = ajustar(ganador, y, ordenes.get(ganador))  # re-ajuste con los 72 meses
    r = pd.Series(np.asarray(final.resid), index=y.index)
    if ganador.startswith("ARIMA"):
        r = r.iloc[1:]  # el primer residuo de ARIMA arrastra la inicialización
    lb = acorr_ljungbox(r, lags=[6, 12, 24])
    mitad = len(r) // 2
    lev = stats.levene(r[:mitad], r[mitad:])
    sh = stats.shapiro(r)
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.5))
    axs[0].plot(r.index, r, lw=1)
    axs[0].axhline(0, c="gray")
    axs[0].set_title("Residuos en el tiempo")
    plot_acf(r, lags=24, ax=axs[1], title="ACF de residuos")
    stats.probplot(r, plot=axs[2])
    axs[2].set_title("Q-Q normal de residuos")
    fig.tight_layout()
    fig.savefig(SALIDA / "07_residuos.png", dpi=120)
    plt.close(fig)
    res["residuos"] = {
        "modelo": ganador,
        "ljung_box_p": {int(k): round(float(v), 4) for k, v in zip([6, 12, 24], lb["lb_pvalue"], strict=False)},
        "levene_mitades_p": round(float(lev.pvalue), 4),
        "var_1a_mitad": round(float(r[:mitad].var()), 2), "var_2a_mitad": round(float(r[mitad:].var()), 2),
        "shapiro_p": round(float(sh.pvalue), 4),
    }

    # ------------------------------------------------------------ 8 · pronóstico 2024
    f = pronosticar(final, H_FUTURO, y.index[-1] + pd.offsets.MonthBegin(1))
    f["inf"] = f["inf"].clip(lower=0)  # un conteo no puede ser negativo
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(y.index, y, "k-", lw=1, label="Histórico 2018-2023")
    ax.plot(f.index, f["media"], "C3-o", ms=3, lw=2, label=f"Pronóstico {ganador_fila['modelo']}")
    ax.fill_between(f.index, f["inf"], f["sup"], color="C3", alpha=0.2, label="Intervalo de predicción 95 %")
    ax.set(title="Pronóstico de suicidios por mes, Colima 2024", ylabel="suicidios")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(SALIDA / "08_pronostico_2024.png", dpi=120)
    plt.close(fig)

    salida = pd.DataFrame({
        "periodo": f.index.strftime("%Y-%m"),
        "modelo": ganador_fila["modelo"],
        "pronostico": f["media"].round(2).values,
        "limite_inferior_95": f["inf"].round(2).values,
        "limite_superior_95": f["sup"].round(2).values,
        "fuente_entrada": "data/oro/serie_mensual_colima.csv",
        "meses_entrenamiento": len(y),
    })
    salida.to_csv(SALIDA_ORO, index=False)
    res["pronostico_2024"] = {
        "total_anual": round(float(f["media"].sum()), 1),
        "promedio_mensual": round(float(f["media"].mean()), 2),
        "rango_mensual_95": [round(float(f["inf"].mean()), 2), round(float(f["sup"].mean()), 2)],
        "total_2023_real": int(y["2023"].sum()),
    }


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    s = cargar()
    res: dict = {"entrada": str(ENTRADA.relative_to(RAIZ)), "prueba": "ene-dic 2023 (12 meses)"}
    caracterizar(s, res)
    modelar(s, res)
    (SALIDA / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
