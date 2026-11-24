"""Pruebas automáticas del observatorio (las corre la CI en cada push).

Lo más importante es test_reproducibilidad. Corre el pipeline completo
(Bronce -> Plata -> Oro -> geoespacial -> diccionario) con los archivos de
Bronce versionados en el repo y compara cada tabla Oro contra la que está
guardada. Así se comprueba el criterio del Sello TDL: "un tercero clona el
repositorio y obtiene los mismos resultados".

Las pruebas que regeneran archivos guardan antes una copia de todo lo que el
pipeline escribe y la restauran al final. Por eso correrlas en una máquina
local no deja cambios en git.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import comun
import diccionario_oro
import geoespacial
import multivariado
import oro
import plata
import pronostico
import verificar_linaje

RAIZ = comun.RAIZ
SALIDAS = [RAIZ / "data" / "plata", RAIZ / "data" / "oro", RAIZ / "data" / "cuarentena",
           RAIZ / "docs" / "E1", RAIZ / "docs" / "E2", RAIZ / "docs" / "E3"]


@pytest.fixture(scope="module")
def respaldo(tmp_path_factory):
    """Copia todo lo que el pipeline sobrescribe y lo restaura al terminar."""
    copia = tmp_path_factory.mktemp("respaldo")
    for d in SALIDAS:
        shutil.copytree(d, copia / d.relative_to(RAIZ))
    yield copia
    for d in SALIDAS:
        shutil.rmtree(d)
        shutil.copytree(copia / d.relative_to(RAIZ), d)


def leer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def iguales(a: pd.DataFrame, b: pd.DataFrame) -> None:
    """Compara como texto. Las columnas numéricas se comparan con tolerancia 1e-9,
    porque el último decimal de una reproyección puede variar entre sistemas operativos."""
    assert list(a.columns) == list(b.columns)
    assert len(a) == len(b)
    for c in a.columns:
        na, nb = pd.to_numeric(a[c], errors="coerce"), pd.to_numeric(b[c], errors="coerce")
        if na.notna().all() and nb.notna().all():
            np.testing.assert_allclose(na, nb, rtol=1e-9, atol=1e-9, err_msg=c)
        else:
            assert (a[c] == b[c]).all(), c


# --------------------------------------------------------------------- pipeline completo
def test_reproducibilidad(respaldo):
    plata.main()
    oro.main()
    geoespacial.main()
    for ruta in sorted((respaldo / "data" / "oro").glob("*.csv")):
        if ruta.name in {"pronostico_suicidio_colima.csv", "diccionario_oro.csv", "localidades_colima.csv"}:
            continue  # se regeneran en las pruebas de abajo
        iguales(leer(RAIZ / "data" / "oro" / ruta.name), leer(ruta))
    for ruta in sorted((respaldo / "data" / "plata").glob("*.csv")):
        iguales(leer(RAIZ / "data" / "plata" / ruta.name), leer(ruta))


def test_linaje_completo(respaldo):
    # verificar_linaje termina con SystemExit(1) si una fila Oro no llega a Bronce
    verificar_linaje.main()


def test_diccionario_documenta_todo(respaldo):
    diccionario_oro.main()  # sale con error si hay una columna sin documentar
    d = pd.read_csv(RAIZ / "data" / "oro" / "diccionario_oro.csv")
    assert d["nulos_pct"].mean() <= 5, "completitud de Oro por debajo del 95 % (umbral del Sello)"


def test_diccionario_rechaza_columna_nueva():
    with pytest.raises(KeyError):
        diccionario_oro.describir("columna_que_nadie_documento")
    assert "min-max" in diccionario_oro.describir("suicidio_minmax")[0]


# --------------------------------------------------------------------- pronóstico
def test_pronostico_reproducible(respaldo):
    pronostico.main()
    nuevo = leer(RAIZ / "data" / "oro" / "pronostico_suicidio_colima.csv")
    iguales(nuevo, leer(respaldo / "data" / "oro" / "pronostico_suicidio_colima.csv"))
    p = pd.to_numeric(nuevo["pronostico"])
    assert (pd.to_numeric(nuevo["limite_inferior_95"]) <= p).all()
    assert (p <= pd.to_numeric(nuevo["limite_superior_95"])).all()
    assert (pd.to_numeric(nuevo["limite_inferior_95"]) >= 0).all(), "un conteo no puede ser negativo"


def test_metricas_error():
    real = pd.Series([2.0, 4.0])
    m = pronostico.metricas(real, pd.Series([3.0, 4.0]))
    assert m == {"MAE": 0.5, "RMSE": round(np.sqrt(0.5), 3), "MAPE_%": 25.0}


def test_arima_reconoce_ruido_blanco():
    rng = np.random.default_rng(1)
    y = pd.Series(rng.normal(5, 1, 80), index=pd.date_range("2018-01-01", periods=80, freq="MS"))
    orden, tabla = pronostico.elegir_arima(y, d=0)
    assert orden[1] == 0 and len(tabla) == 16


# --------------------------------------------------------------------- multivariado (E3)
def test_multivariado_reproducible(respaldo):
    multivariado.main()
    iguales(leer(RAIZ / "data" / "oro" / "localidades_colima.csv"),
            leer(respaldo / "data" / "oro" / "localidades_colima.csv"))


def test_mardia_detecta_normal_y_no_normal():
    rng = np.random.default_rng(7)
    normal = rng.normal(size=(400, 3))
    assert multivariado.mardia(normal)["asimetria_p"] > 0.01
    sesgada = rng.exponential(size=(400, 3))
    assert multivariado.mardia(sesgada)["asimetria_p"] < 0.001


def test_pillai_y_permutacion():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(60, 3))
    g = np.repeat(["a", "b"], 30)
    x[g == "b"] += 1.5  # grupos claramente distintos
    assert multivariado.permutacion_pillai(x, g, n_perm=199)["p"] < 0.05
    assert 0 <= multivariado.pillai(x, g) <= 1


def test_coordenada_gms():
    assert abs(multivariado.gms_a_decimal("18°56'13.462\" N") - 18.937073) < 1e-5
    assert multivariado.gms_a_decimal("103°57'53.990\" W") < 0


# --------------------------------------------------------------------- utilidades Bronce
def test_sha256(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"observatorio")
    assert comun.sha256(f) == hashlib.sha256(b"observatorio").hexdigest()


class _RespuestaFalsa:
    def __init__(self, tipo: str):
        self.headers = {"Content-Type": tipo}

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield b"datos"

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_descarga_rechaza_html(monkeypatch, tmp_path):
    """INEGI responde 200 con una página HTML cuando el archivo no existe: no debe
    guardarse como si fueran datos."""
    monkeypatch.setattr(comun.requests, "get", lambda *a, **k: _RespuestaFalsa("text/html"))
    with pytest.raises(ValueError, match="HTML"):
        comun.descargar("https://ejemplo/x.zip", tmp_path / "x.zip")


def test_descarga_guarda_binario(monkeypatch, tmp_path):
    monkeypatch.setattr(comun.requests, "get", lambda *a, **k: _RespuestaFalsa("application/zip"))
    destino = comun.descargar("https://ejemplo/x.zip", tmp_path / "x.zip")
    assert destino.read_bytes() == b"datos"


# --------------------------------------------------------------------- huella HTTP (optimización E3)
class _RespuestaParcial(_RespuestaFalsa):
    def __init__(self, status=206, etag='"abc"', total="1000", tipo="application/zip"):
        super().__init__(tipo)
        self.status_code = status
        self.headers.update({"ETag": etag, "Content-Range": f"bytes 0-0/{total}", "Last-Modified": "x"})


def test_huella_igual_evita_descarga(monkeypatch, tmp_path):
    monkeypatch.setattr(comun, "HUELLAS", tmp_path / "huellas.csv")
    monkeypatch.setattr(comun.requests, "get", lambda *a, **k: _RespuestaParcial())
    igual, h = comun.sin_cambios("https://ejemplo/x.zip")
    assert not igual, "sin huella previa siempre se descarga"
    comun.guardar_huella("https://ejemplo/x.zip", h)
    assert comun.sin_cambios("https://ejemplo/x.zip")[0], "misma huella: no se descarga"


def test_huella_distinta_o_sin_soporte_descarga(monkeypatch, tmp_path):
    monkeypatch.setattr(comun, "HUELLAS", tmp_path / "huellas.csv")
    monkeypatch.setattr(comun.requests, "get", lambda *a, **k: _RespuestaParcial())
    comun.guardar_huella("u", comun.huella_remota("u"))
    monkeypatch.setattr(comun.requests, "get", lambda *a, **k: _RespuestaParcial(total="2000"))
    assert not comun.sin_cambios("u")[0], "cambió el tamaño: se descarga"
    monkeypatch.setattr(comun.requests, "get", lambda *a, **k: _RespuestaParcial(status=200, tipo="text/html"))
    assert comun.huella_remota("u") is None
    assert not comun.sin_cambios("u")[0], "servidor sin soporte: ante la duda se descarga"


def test_huella_otro_servidor_mismo_archivo(monkeypatch, tmp_path):
    """El INEGI sirve copias desde varios servidores: otro ETag y una fecha que difiere
    por segundos, pero el mismo tamaño. Debe contar como el mismo archivo."""
    monkeypatch.setattr(comun, "HUELLAS", tmp_path / "huellas.csv")
    a = _RespuestaParcial(etag='"servidor1"')
    a.headers["Last-Modified"] = "Mon, 10 Nov 2025 12:00:15 GMT"
    b = _RespuestaParcial(etag='"servidor2"')
    b.headers["Last-Modified"] = "Mon, 10 Nov 2025 12:00:25 GMT"
    monkeypatch.setattr(comun.requests, "get", lambda *x, **k: a)
    comun.guardar_huella("u", comun.huella_remota("u"))
    monkeypatch.setattr(comun.requests, "get", lambda *x, **k: b)
    assert comun.sin_cambios("u")[0]
    b.headers["Last-Modified"] = "Tue, 21 Jul 2026 22:00:03 GMT"  # publicación nueva
    assert not comun.sin_cambios("u")[0]
