"""E2 — Fuente especializada geoespacial: DENUE + Marco Geoestadístico con GeoPandas.

1. Valida la ubicación: ¿el punto de cada consultorio cae dentro del municipio
   que declara DENUE? (unión espacial punto-en-polígono).
2. Competencia cercana a la cliente: consultorios de psicología a 500 m, 1 km y
   2 km del centro histórico de Colima (se usa un punto PÚBLICO de referencia, el
   Jardín Libertad, nunca la dirección del consultorio de la cliente).
3. Mapas: oferta vs. necesidad por municipio y competencia en el centro.

Salidas:
    data/oro/consultorios_psicologia_geo.csv / .geojson   puntos con linaje
    data/oro/competencia_centro_colima.csv                conteos por radio
    docs/E2/mapa_oferta_necesidad.png, docs/E2/mapa_centro_colima.png
    (agrega sus filas a data/oro/linaje_oro.csv)

Uso:  python src/geoespacial.py   (después de src/oro.py)
"""
from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402

from comun import RAIZ  # noqa: E402

PLATA = RAIZ / "data" / "plata"
ORO = RAIZ / "data" / "oro"
DOCS = RAIZ / "docs" / "E2"
SHP = RAIZ / "data" / "bronce" / "inegi_marcogeo2020" / "06mun.shp"

CRS_METRICO = 6372  # Mexico ITRF2008 / LCC (el mismo del Marco Geoestadístico), en metros
CENTRO = (-103.7250, 19.2433)  # Jardín Libertad, centro histórico de Colima (lon, lat)
RADIOS_M = [500, 1000, 2000]
CONTINENTAL = box(-104.8, 18.6, -103.4, 19.6)  # excluye el archipiélago de Revillagigedo

# Paleta (rampas de un solo tono, de claro a oscuro) y tinta
SUPERFICIE, TINTA, TINTA_2, TENUE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
NARANJA = ["#fde3d6", "#f8bfa3", "#f39670", "#eb6834", "#c8501f", "#9c3c15", "#6e2a0e"]
PUNTO = "#2a78d6"


def cargar() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame]:
    mun = gpd.read_file(SHP).rename(columns={"CVE_MUN": "cve_mun"})
    den = pd.read_csv(PLATA / "denue.csv", dtype=str, keep_default_na=False)
    psic = den[den["es_psicologia"] == "True"].copy()
    pts = gpd.GeoDataFrame(psic, geometry=gpd.points_from_xy(psic["longitud"].astype(float),
                                                             psic["latitud"].astype(float)), crs=4326)
    ind = pd.read_csv(ORO / "municipios_colima.csv", dtype={"cve_mun": str})
    return mun.to_crs(CRS_METRICO), pts.to_crs(CRS_METRICO), ind


def validar_ubicacion(mun: gpd.GeoDataFrame, pts: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    j = gpd.sjoin(pts, mun[["cve_mun", "geometry"]].rename(columns={"cve_mun": "cve_mun_geo"}),
                  how="left", predicate="within").drop(columns="index_right")
    j["ubicacion_consistente"] = j["cve_mun"] == j["cve_mun_geo"]
    return j


def competencia(pts: gpd.GeoDataFrame) -> tuple[pd.DataFrame, gpd.GeoSeries]:
    centro = gpd.GeoSeries([Point(CENTRO)], crs=4326).to_crs(CRS_METRICO)
    dist = pts.geometry.distance(centro.iloc[0])
    filas = []
    for r in RADIOS_M:
        dentro = pts[dist <= r]
        filas.append({"radio_m": r, "consultorios_psic": len(dentro),
                      "privados": int((dentro["sector"] == "privado").sum()),
                      "publicos": int((dentro["sector"] == "publico").sum()),
                      "pct_del_municipio_colima": round(100 * len(dentro) / (pts["cve_mun"] == "002").sum(), 1),
                      "n_registros_fuente": len(dentro),
                      "fecha_ingesta_max": dentro["fecha_ingesta_utc"].max() if len(dentro) else pd.NA})
    return pd.DataFrame(filas), dist


# Desplazamiento manual (metros) de etiquetas en la zona metropolitana, donde los
# municipios son pequeños y las etiquetas chocan. Con línea guía hacia el municipio.
DESPLAZA = {"008": (-14000, 4000), "010": (-16000, -9000), "003": (2000, 9000), "004": (-15000, -12000), "001": (-4000, -10000)}


def etiqueta(ax, geom, texto, tam=7.5, desplaza=None):
    p = geom.representative_point()
    caja = dict(boxstyle="round,pad=0.15", fc=SUPERFICIE, ec="none", alpha=0.85)
    if desplaza:
        ax.annotate(texto, (p.x, p.y), xytext=(p.x + desplaza[0], p.y + desplaza[1]), ha="center", va="center",
                    fontsize=tam, color=TINTA, bbox=caja,
                    arrowprops=dict(arrowstyle="-", color=TINTA_2, lw=0.8, shrinkA=0, shrinkB=2))
    else:
        ax.annotate(texto, (p.x, p.y), ha="center", va="center", fontsize=tam, color=TINTA, bbox=caja)


def mapa_oferta_necesidad(mun: gpd.GeoDataFrame, ind: pd.DataFrame, pts: gpd.GeoDataFrame) -> None:
    g = mun.merge(ind, on="cve_mun")
    g = gpd.clip(g.to_crs(4326), CONTINENTAL).to_crs(CRS_METRICO)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), facecolor=SUPERFICIE)
    paneles = [("consultorios_por_100k", AZUL, "Oferta: consultorios de psicología\npor cada 100 mil habitantes (DENUE 2026)"),
               ("tasa_suicidio_anual_100k", NARANJA, "Necesidad: suicidios por año\npor cada 100 mil habitantes (2018–2023)")]
    for ax, (col, rampa, titulo) in zip(axes, paneles, strict=False):
        cmap = LinearSegmentedColormap.from_list(col, rampa)
        g.plot(column=col, cmap=cmap, ax=ax, edgecolor=SUPERFICIE, linewidth=1.5, legend=True,
               legend_kwds={"shrink": 0.6, "orientation": "horizontal", "pad": 0.02})
        for _, r in g.iterrows():
            corto = {"Villa de Álvarez": "V. de Álvarez"}.get(r["nom_mun"], r["nom_mun"])
            etiqueta(ax, r.geometry, f"{corto}\n{r[col]:.1f}", 7.5, DESPLAZA.get(r["cve_mun"]))
        ax.set_title(titulo, fontsize=11, color=TINTA, loc="left")
        ax.set_axis_off()
        cb = ax.get_figure().axes[-1]
        cb.tick_params(labelsize=8, colors=TINTA_2)
    fig.suptitle("Colima: dónde hay necesidad de atención en salud mental y dónde hay consultorios",
                 fontsize=13, color=TINTA, x=0.02, ha="left")
    fig.text(0.02, 0.02, "Fuentes: INEGI — DENUE, Estadística de Defunciones Registradas, Censo 2020 y Marco "
             "Geoestadístico 2020. Tasas de municipios pequeños (Ixtlahuacán, Minatitlán) son inestables.",
             fontsize=8, color=TINTA_2)
    fig.savefig(DOCS / "mapa_oferta_necesidad.png", dpi=160, bbox_inches="tight", facecolor=SUPERFICIE)
    plt.close(fig)


def mapa_centro(mun: gpd.GeoDataFrame, pts: gpd.GeoDataFrame, comp: pd.DataFrame) -> None:
    centro = gpd.GeoSeries([Point(CENTRO)], crs=4326).to_crs(CRS_METRICO).iloc[0]
    fig, ax = plt.subplots(figsize=(8.5, 8.5), facecolor=SUPERFICIE)
    mun.boundary.plot(ax=ax, color=TENUE, linewidth=1)
    for r, estilo in zip(RADIOS_M, [(0, (1, 2)), (0, (4, 3)), "solid"], strict=False):
        gpd.GeoSeries([centro.buffer(r)]).boundary.plot(ax=ax, color=TINTA_2, linewidth=1, linestyle=estilo)
    conteos = "\n".join(
        f"{'Punteado' if r == 500 else 'Guiones' if r == 1000 else 'Continuo'} · {r if r < 1000 else r // 1000}"
        f"{' m' if r < 1000 else ' km'}: {comp.loc[comp['radio_m'] == r, 'consultorios_psic'].item()} consultorios"
        for r in RADIOS_M)
    ax.text(0.02, 0.98, "Consultorios dentro de cada radio\n" + conteos, transform=ax.transAxes, va="top",
            fontsize=9, color=TINTA, linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.5", fc=SUPERFICIE, ec=TENUE, lw=0.8))
    priv = pts[pts["sector"] == "privado"]
    pub = pts[pts["sector"] == "publico"]
    priv.plot(ax=ax, color=PUNTO, markersize=34, edgecolor=SUPERFICIE, linewidth=1.2, zorder=3)
    pub.plot(ax=ax, color=PUNTO, marker="s", markersize=40, edgecolor=SUPERFICIE, linewidth=1.2, zorder=3)
    ax.plot(centro.x, centro.y, marker="*", color=TINTA, markersize=14, zorder=4)
    lado = 5200
    ax.set_xlim(centro.x - lado, centro.x + lado)
    ax.set_ylim(centro.y - lado, centro.y + lado)
    ax.set_axis_off()
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=PUNTO, markeredgecolor=SUPERFICIE, markersize=8, label="Consultorio de psicología privado"),
        Line2D([], [], marker="s", ls="", color=PUNTO, markeredgecolor=SUPERFICIE, markersize=8, label="Consultorio de psicología público"),
        Line2D([], [], marker="*", ls="", color=TINTA, markersize=12, label="Jardín Libertad (centro histórico)"),
        Line2D([], [], color=TENUE, label="Límite municipal (Colima / Villa de Álvarez)"),
    ], loc="lower left", fontsize=8.5, frameon=True, facecolor=SUPERFICIE, edgecolor="none", labelcolor=TINTA)
    n1 = comp.loc[comp["radio_m"] == 1000, "consultorios_psic"].item()
    ax.set_title(f"Competencia en el centro de Colima: {n1} consultorios de psicología a 1 km o menos",
                 fontsize=12, color=TINTA, loc="left")
    fig.text(0.02, 0.02, "Fuente: INEGI — DENUE (descarga masiva Colima) y Marco Geoestadístico 2020. "
             "Sin nombres ni datos de contacto.", fontsize=8, color=TINTA_2)
    fig.savefig(DOCS / "mapa_centro_colima.png", dpi=160, bbox_inches="tight", facecolor=SUPERFICIE)
    plt.close(fig)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    mun, pts, ind = cargar()
    pts = validar_ubicacion(mun, pts)
    comp, dist = competencia(pts)
    pts["distancia_centro_m"] = dist.round(0)

    # Oro geoespacial con linaje en cada fila
    cols = ["id_registro", "clee", "codigo_act", "sector", "cve_mun", "cve_mun_geo", "ubicacion_consistente",
            "per_ocu", "fecha_alta", "latitud", "longitud", "distancia_centro_m",
            "archivo_bronce", "fila_bronce", "fecha_ingesta_utc"]
    geo = pts[cols].assign(n_registros_fuente=1, fecha_ingesta_max=pts["fecha_ingesta_utc"])
    geo.to_csv(ORO / "consultorios_psicologia_geo.csv", index=False, encoding="utf-8", lineterminator="\n")
    gpd.GeoDataFrame(geo, geometry=pts.geometry, crs=CRS_METRICO).to_crs(4326).to_file(
        ORO / "consultorios_psicologia_colima.geojson", driver="GeoJSON")
    comp.to_csv(ORO / "competencia_centro_colima.csv", index=False, encoding="utf-8", lineterminator="\n")

    # Linaje: se reemplazan las filas de estas tablas (para que la corrida sea idempotente)
    ruta_lin = ORO / "linaje_oro.csv"
    lin = pd.read_csv(ruta_lin, dtype=str)
    lin = lin[~lin["tabla_oro"].isin(["consultorios_psicologia_geo", "competencia_centro_colima"])]
    nuevos = [pd.DataFrame({"tabla_oro": "consultorios_psicologia_geo", "clave_oro": pts["id_registro"],
                            "id_registro": pts["id_registro"], "archivo_bronce": pts["archivo_bronce"],
                            "fila_bronce": pts["fila_bronce"], "fecha_ingesta_utc": pts["fecha_ingesta_utc"]})]
    for r in RADIOS_M:
        d = pts[pts["distancia_centro_m"] <= r]
        nuevos.append(pd.DataFrame({"tabla_oro": "competencia_centro_colima", "clave_oro": str(r),
                                    "id_registro": d["id_registro"], "archivo_bronce": d["archivo_bronce"],
                                    "fila_bronce": d["fila_bronce"], "fecha_ingesta_utc": d["fecha_ingesta_utc"]}))
    pd.concat([lin, *nuevos]).to_csv(ruta_lin, index=False, encoding="utf-8", lineterminator="\n")

    mapa_oferta_necesidad(mun, ind, pts)
    mapa_centro(mun, pts, comp)

    inconsistentes = pts[~pts["ubicacion_consistente"]]
    print(comp.to_string(index=False))
    print(f"Ubicación DENUE vs. polígono: {len(pts) - len(inconsistentes)} de {len(pts)} consistentes")
    if len(inconsistentes):
        print(inconsistentes[["id_registro", "cve_mun", "cve_mun_geo"]].to_string(index=False))


if __name__ == "__main__":
    main()
