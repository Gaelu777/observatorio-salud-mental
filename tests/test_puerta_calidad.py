"""Prueba de la Puerta de Calidad: inyecta registros inválidos y verifica que
terminen en cuarentena con el motivo correcto (y que los válidos pasen).

Uso:  python tests/test_puerta_calidad.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from plata import ESQUEMA_DEF, puerta_calidad  # noqa: E402


def registro_valido(i: int) -> dict:
    return {"id_registro": f"T:{i}", "archivo_bronce": "prueba", "fila_bronce": i,
            "ent_resid": "06", "mun_resid": "002", "ent_ocurr": "06", "mun_ocurr": "002",
            "causa_def": "X700", "sexo": "H", "edad_anios": 30, "dia_ocurr": 15, "mes_ocurr": 6,
            "anio_ocur": 2021, "mes_regis": 7, "anio_regis": 2021, "tipo_defun": 3,
            "fecha_ingesta_utc": "2026-01-01T00:00:00Z", "sha256_origen": "x"}


def test_puerta_calidad_cuarentena() -> None:
    casos = {  # fila -> (cambio, texto esperado en el motivo)
        1: ({"causa_def": "ZZZ"}, "causa_def"),
        2: ({"edad_anios": 150}, "edad_anios"),
        3: ({"mes_ocurr": 2, "dia_ocurr": 31}, "regla fecha_ocurrencia_valida"),
        4: ({"anio_ocur": 2030}, "regla ocurrencia<=registro"),
        5: ({"sexo": "7"}, "sexo"),
    }
    filas = [registro_valido(i) for i in range(7)]  # 0 y 6 quedan válidas
    # Faltantes legítimos (desconocidos de INEGI) NO deben ir a cuarentena
    filas[6].update({"mes_ocurr": None, "sexo": None, "edad_anios": None})
    for i, (cambio, _) in casos.items():
        filas[i].update(cambio)
    df = pd.DataFrame(filas)
    for c in ["edad_anios", "dia_ocurr", "mes_ocurr", "anio_ocur", "mes_regis", "anio_regis", "tipo_defun"]:
        df[c] = pd.to_numeric(df[c]).astype("Int64")
    df["sexo"] = df["sexo"].replace({None: np.nan})

    validos, cuarentena = puerta_calidad(df, ESQUEMA_DEF, "prueba")
    assert set(validos["fila_bronce"]) == {0, 6}, validos["fila_bronce"].tolist()
    assert len(validos) + len(cuarentena) == len(df), "se perdieron registros"
    for i, (_, esperado) in casos.items():
        motivo = cuarentena.loc[cuarentena["fila_bronce"] == i, "motivo"].item()
        assert esperado in motivo, (i, motivo)
        print(f"OK fila {i}: {motivo}")
    print("OK: los faltantes legítimos pasan; los 5 inválidos van a cuarentena con motivo.")


if __name__ == "__main__":
    test_puerta_calidad_cuarentena()
