"""Prueba de humo del tablero: corre la app completa sin navegador y
verifica que no lance excepciones y que muestre los titulares."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / "tablero" / "app.py"


def test_tablero_carga_sin_errores():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception, at.exception
    assert len(at.metric) >= 4
    assert len(at.tabs) == 4
