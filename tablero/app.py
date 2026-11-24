"""Tablero del Observatorio de Servicios Psicológicos · Colima.

Lee solo la capa Oro (y la bitácora de capturas). No recalcula nada: si el
pipeline programado actualiza Oro, el tablero muestra los datos nuevos al
recargar la página.

Uso local:  streamlit run tablero/app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
ORO = RAIZ / "data" / "oro"

# Paleta categórica validada (slots 1 y 2) y tinta de texto
AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#52514e"
COLOR_ZONA = alt.Scale(domain=["metropolitana", "resto"], range=[AZUL, NARANJA])

st.set_page_config(page_title="Observatorio de Servicios Psicológicos · Colima", layout="wide")


@st.cache_data
def cargar(nombre: str, **kw) -> pd.DataFrame:
    return pd.read_csv(ORO / nombre, **kw)


def leer_json(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


serie = cargar("serie_mensual_colima.csv")
prono = cargar("pronostico_suicidio_colima.csv")
mun = cargar("municipios_colima.csv", dtype={"cve_mun": str})
loc = cargar("localidades_colima.csv", dtype={"cve_mun": str})
cons = cargar("consultorios_psicologia_geo.csv", dtype={"cve_mun": str})
comp = cargar("competencia_centro_colima.csv")
res_pron = leer_json(RAIZ / "docs" / "E1" / "pronostico" / "resumen.json")
res_mv = leer_json(RAIZ / "docs" / "E3" / "multivariado" / "resumen.json")

st.title("Observatorio de Servicios Psicológicos · Colima")
st.caption("Datos públicos y agregados del INEGI (Defunciones, DENUE, Censo 2020, Marco Geoestadístico). "
           f"Última captura en Oro: {serie['fecha_ingesta_max'].max()[:10]}.")

# --------------------------------------------------------------------------- titulares
c1, c2, c3, c4 = st.columns(4)
c1.metric("Consultorios de psicología en el estado", int(mun["consultorios_psic"].sum()))
c2.metric("A 1 km del centro de Colima", int(comp.loc[comp["radio_m"] == 1000, "consultorios_psic"].iloc[0]))
c3.metric("Suicidios esperados en 2024", f"≈ {prono['pronostico'].sum():.0f}",
          help="Pronóstico del modelo ganador; intervalo anual aprox. 38 a 71")
lejos = loc[loc["dist_psicologo_km"] > 10]
c4.metric("Personas a más de 10 km de un psicólogo", f"{lejos['pobtot'].sum():,}",
          help=f"{len(lejos)} localidades de 500 habitantes o más")

tab_pron, tab_oferta, tab_mapa, tab_calidad = st.tabs(
    ["Pronóstico", "Oferta y necesidad", "Mapa multivariado", "Calidad del sistema"])

# --------------------------------------------------------------------------- pronóstico
with tab_pron:
    st.subheader("¿Cuántos suicidios se esperan por mes en Colima?")
    hist = serie[["periodo", "suicidio"]].rename(columns={"suicidio": "valor"})
    hist["fecha"] = pd.to_datetime(hist["periodo"])
    fut = prono.assign(fecha=pd.to_datetime(prono["periodo"]))
    base = alt.Chart(hist).encode(x=alt.X("fecha:T", title=None))
    linea = base.mark_line(strokeWidth=2, color=AZUL).encode(
        y=alt.Y("valor:Q", title="suicidios por mes"),
        tooltip=[alt.Tooltip("periodo:N", title="Mes"), alt.Tooltip("valor:Q", title="Registrados")])
    puntos = base.mark_circle(size=40, color=AZUL).encode(y="valor:Q", tooltip=["periodo:N", "valor:Q"])
    banda = alt.Chart(fut).mark_area(opacity=0.2, color=NARANJA).encode(
        x="fecha:T", y="limite_inferior_95:Q", y2="limite_superior_95:Q")
    pr = alt.Chart(fut).mark_line(strokeWidth=2, color=NARANJA, strokeDash=[6, 3]).encode(
        x="fecha:T", y="pronostico:Q",
        tooltip=[alt.Tooltip("periodo:N", title="Mes"), alt.Tooltip("pronostico:Q", title="Pronóstico", format=".1f"),
                 alt.Tooltip("limite_inferior_95:Q", title="Mínimo 95 %", format=".1f"),
                 alt.Tooltip("limite_superior_95:Q", title="Máximo 95 %", format=".1f")])
    st.altair_chart((banda + linea + puntos + pr).properties(height=340), use_container_width=True)
    st.caption("Azul: registrados (INEGI, 2018-2023). Naranja: pronóstico 2024 con intervalo del 95 %.")

    st.info(
        "**Qué significa:** en Colima se registran en promedio entre 4 y 5 suicidios al mes y para 2024 se esperan "
        "alrededor de 54 en el año. Cualquier mes puede tener entre 0 y 9 sin que eso anuncie una tendencia. "
        "**No se detecta un mes del año con riesgo claramente mayor**, así que la prevención y la difusión de "
        "servicios conviene sostenerlas todo el año. La excepción fue 2021 (75 casos), después del confinamiento.")
    if res_pron:
        tabla = pd.DataFrame(res_pron["comparacion"]).drop(columns=["clave"])
        with st.expander("¿Cómo se eligió el modelo? (error en 2023, datos que el modelo no vio)"):
            st.dataframe(tabla, hide_index=True, use_container_width=True)
            st.markdown(f"Ganador: **{res_pron['ganador']}** (menor RMSE). Ljung-Box de residuos "
                        f"p = {res_pron['residuos']['ljung_box_p']['12']} (sin autocorrelación). "
                        "Detalle en `docs/E1/pronostico.md`.")

# --------------------------------------------------------------------------- oferta
with tab_oferta:
    st.subheader("¿Dónde hay consultorios y dónde hay necesidad?")
    izq, der = st.columns([3, 2])
    with izq:
        capa = pdk.Layer("ScatterplotLayer", data=cons, get_position="[longitud, latitud]",
                         get_fill_color=[42, 120, 214, 190], get_radius=250, pickable=True,
                         stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1)
        vista = pdk.ViewState(latitude=19.15, longitude=-103.95, zoom=8.2)
        st.pydeck_chart(pdk.Deck(layers=[capa], initial_view_state=vista, map_style=None,
                                 tooltip={"text": "Sector: {sector}\nAlta en DENUE: {fecha_alta}\n"
                                                  "A {distancia_centro_m} m del centro de Colima"}))
        st.caption("Cada punto es un consultorio de psicología registrado en el DENUE (sin nombres ni datos personales).")
    with der:
        t = mun[["nom_mun", "pobtot", "consultorios_psic", "consultorios_por_100k",
                 "tasa_suicidio_anual_100k", "oferta_nivel", "necesidad_nivel"]].sort_values("consultorios_por_100k")
        st.dataframe(t.rename(columns={"nom_mun": "Municipio", "pobtot": "Población", "consultorios_psic": "Consultorios",
                                       "consultorios_por_100k": "Por 100 mil hab.",
                                       "tasa_suicidio_anual_100k": "Suicidios/100 mil/año",
                                       "oferta_nivel": "Oferta", "necesidad_nivel": "Necesidad"}),
                     hide_index=True, use_container_width=True, height=390)
    st.markdown("**Competencia directa en el centro de Colima**")
    st.dataframe(comp[["radio_m", "consultorios_psic", "privados", "publicos", "pct_del_municipio_colima"]].rename(
        columns={"radio_m": "Radio (m)", "consultorios_psic": "Consultorios", "privados": "Privados",
                 "publicos": "Públicos", "pct_del_municipio_colima": "% del municipio"}), hide_index=True)

# --------------------------------------------------------------------------- mapa PCA
with tab_mapa:
    st.subheader("Mapa de localidades: acceso a psicólogos vs vulnerabilidad del hogar")
    zonas = st.multiselect("Zona", ["metropolitana", "resto"], default=["metropolitana", "resto"])
    d = loc[loc["zona"].isin(zonas)]
    puntos = alt.Chart(d).mark_circle(opacity=0.8, stroke="white", strokeWidth=1).encode(
        x=alt.X("cp1:Q", title="CP1 · Urbanización y acceso a psicólogos  →  más acceso"),
        y=alt.Y("cp2:Q", title="CP2 · Vulnerabilidad del hogar  →  más vulnerable"),
        color=alt.Color("zona:N", scale=COLOR_ZONA, legend=alt.Legend(title="Zona", orient="top")),
        size=alt.Size("pobtot:Q", scale=alt.Scale(range=[40, 900]), legend=None),
        tooltip=[alt.Tooltip("nom_loc:N", title="Localidad"), alt.Tooltip("nom_mun:N", title="Municipio"),
                 alt.Tooltip("pobtot:Q", title="Habitantes", format=","),
                 alt.Tooltip("dist_psicologo_km:Q", title="Km al psicólogo más cercano", format=".1f"),
                 alt.Tooltip("pct_viv_internet:Q", title="% viviendas con internet", format=".0f"),
                 alt.Tooltip("pct_60ymas:Q", title="% 60 años y más", format=".0f")])
    reglas = alt.Chart(pd.DataFrame({"v": [0]})).mark_rule(color=GRIS, strokeWidth=0.5)
    st.altair_chart((reglas.encode(x="v:Q") + reglas.encode(y="v:Q") + puntos).properties(height=480),
                    use_container_width=True)
    st.info(
        "**Cómo leerlo:** a la derecha están las ciudades con escolaridad, internet y un psicólogo cerca; a la "
        "izquierda, las localidades aisladas. Arriba, hogares más vulnerables (adultos mayores, jefatura femenina, "
        "desempleo). **El cuadrante de arriba a la izquierda es el hueco de oferta.** El caso más claro es "
        "Cerro de Ortega (Tecomán): unos 9,300 habitantes y el consultorio registrado más cercano a 24 km. La costa "
        "de Tecomán y Armería es la zona con más población sin oferta cercana; el centro de Colima, la de más "
        "competencia.")
    if res_mv:
        z, o = res_mv["manova_zona"], res_mv["manova_oferta"]
        st.caption(f"MANOVA zona: Pillai = {z['estadisticos']['pillai']['valor']}, p por permutación = "
                   f"{z['permutacion']['p']:.4f} · MANOVA nivel de oferta: Pillai = "
                   f"{o['estadisticos']['pillai']['valor']}, p por permutación = {o['permutacion']['p']:.3f}. "
                   "CP1 y CP2 explican el "
                   f"{res_mv['pca']['varianza_acumulada'][1]:.0%} de la variación. Detalle en docs/E3/multivariado.md.")
    with st.expander("Tabla de localidades"):
        st.dataframe(d[["nom_loc", "nom_mun", "pobtot", "dist_psicologo_km", "escolaridad_prom", "pct_viv_internet",
                        "pct_sin_afiliacion", "pct_60ymas", "cp1", "cp2"]].sort_values("cp1"),
                     hide_index=True, use_container_width=True)

# --------------------------------------------------------------------------- calidad
with tab_calidad:
    st.subheader("¿Por qué se puede confiar en estos datos?")
    resumen_plata = leer_json(RAIZ / "data" / "plata" / "resumen_plata.json")
    if resumen_plata:
        filas = [{"Fuente": k, "Bronce": v.get("bronce"), "Plata (válidos)": v.get("plata"),
                  "Cuarentena": v.get("cuarentena")} for k, v in resumen_plata.items() if isinstance(v, dict)]
        st.markdown("**Puerta de calidad (Pandera):** lo que no pasa va a cuarentena con su motivo; nada se borra.")
        st.dataframe(pd.DataFrame(filas), hide_index=True)
    bit = RAIZ / "data" / "bitacora" / "capturas.csv"
    if bit.exists():
        b = pd.read_csv(bit)
        ok = (b["estado"] == "success").mean()
        st.metric("Capturas automáticas exitosas", f"{ok:.0%}", help=f"{len(b)} corridas registradas en la bitácora")
        st.dataframe(b.tail(14), hide_index=True, use_container_width=True)
    lin = cargar("linaje_oro.csv")
    st.markdown(f"**Linaje:** {len(lin):,} enlaces entre filas de Oro y registros de Bronce "
                "(archivo, fila y fecha de captura). Verificación automática en cada corrida.")
