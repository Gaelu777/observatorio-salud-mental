"""E3 · Ingeniería de Datos: optimización medida del pipeline (antes vs. después).

Dos cambios, cada uno medido en tiempo, memoria pico y errores:

  1. CAPTURA (extraer_defunciones.py). Antes: en cada corrida completa se bajaban
     los 6 ZIP del INEGI (~240 MB), aunque no hubieran cambiado; el SHA-256 decía
     después de descargar que eran iguales. Después: se pide solo 1 byte de cada
     archivo y se comparan el ETag y el tamaño contra la última descarga
     (data/bronce/huellas_http.csv). Si coinciden, no se descarga.

  2. LIMPIEZA (plata.py, defunciones). Dos cambios:
     a) leer solo las 14 columnas que se usan, no las 59-74 (factor B, ganador del
        experimento factorial de E2: efecto -1.35 s, el mayor de los tres);
     b) calcular el nombre del archivo una vez y no por cada fila (cuello de botella
        encontrado con cProfile: 24 % del tiempo).

El interruptor OPTIMIZACION_E3=0 reproduce el código anterior para medir el "antes".

Calidad (no se puede degradar): la salida de Plata debe ser idéntica byte a
byte (mismo SHA-256), y Bronce no debe cambiar.

Cada medición corre en un proceso nuevo, para que la memoria pico sea la de
esa corrida y no la acumulada de las anteriores.

Uso:  python src/optimizacion.py              (captura: 1 corrida por condición, por cortesía al INEGI;
                                               limpieza: 5 réplicas por condición, intercaladas)
      python src/optimizacion.py --sin-red    (solo limpieza)
Salida: docs/E3/optimizacion/ (mediciones.csv, resumen.json, comparacion.png)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "E3" / "optimizacion"
REPLICAS_LIMPIEZA = 5


# --------------------------------------------------------------------------- dentro del hijo
def memoria_pico_mb() -> float:
    """Memoria pico (RSS / working set) del proceso actual, en MB."""
    try:
        import resource  # Linux / macOS

        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return r / 1024 if sys.platform != "darwin" else r / 1024 / 1024
    except ImportError:  # Windows
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
        k32.GetCurrentProcess.restype = wintypes.HANDLE  # sin esto el handle se trunca y la llamada falla
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb):
            raise OSError("GetProcessMemoryInfo falló") from None
        return c.PeakWorkingSetSize / 1024 / 1024


def sha(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def hijo(tarea: str) -> None:
    sys.path.insert(0, str(RAIZ / "src"))
    # Las bibliotecas se importan ANTES de arrancar el cronómetro: importar pandas y
    # pandera tarda unos 4-5 s y es igual en ambas condiciones; medirlo escondería
    # la diferencia. La memoria pico sí incluye las bibliotecas (es lo que ocupa el proceso).
    import comun
    import extraer_defunciones as ed
    import plata

    errores, detalle = 0, ""
    mem_base = memoria_pico_mb()
    t0 = time.perf_counter()
    try:
        if tarea == "limpieza":
            r = plata.plata_defunciones()
            detalle = sha(RAIZ / "data" / "plata" / "defunciones.csv")
            errores = r["cuarentena"]
        elif tarea == "captura":
            descargados = {"n": 0, "bytes": 0}
            original = comun.descargar

            def contar(url, destino, **kw):  # cuenta lo que realmente se baja
                p = original(url, destino, **kw)
                descargados["n"] += 1
                descargados["bytes"] += p.stat().st_size
                return p

            ed.descargar = contar
            for i, anio in enumerate(range(2018, 2024)):
                if i:
                    time.sleep(comun.PAUSA_SEG)
                print(ed.procesar_anio(anio), file=sys.stderr, flush=True)
            detalle = f"{descargados['n']} descargas, {descargados['bytes'] / 1e6:.1f} MB"
    except Exception as e:  # noqa: BLE001 - un error ES una medición
        errores, detalle = errores + 1, f"{type(e).__name__}: {e}"
    seg = time.perf_counter() - t0
    pico = memoria_pico_mb()
    print(json.dumps({"seg": round(seg, 3), "mem_mb": round(pico, 1),
                      "mem_trabajo_mb": round(pico - mem_base, 1), "errores": errores, "detalle": detalle}))


# --------------------------------------------------------------------------- padre
def medir(tarea: str, condicion: str, env_extra: dict) -> dict:
    env = {**os.environ, **env_extra, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, __file__, "--hijo", tarea], capture_output=True, text=True, env=env,
                       cwd=RAIZ, check=False)
    linea = [x for x in p.stdout.strip().splitlines() if x.startswith("{")]
    if p.returncode != 0 or not linea:
        r = {"seg": None, "mem_mb": None, "errores": 1, "detalle": p.stderr[-300:]}
    else:
        r = json.loads(linea[-1])
    r.update(tarea=tarea, condicion=condicion)
    print(r, flush=True)
    return r


def main() -> None:
    import pandas as pd

    SALIDA.mkdir(parents=True, exist_ok=True)
    filas = []
    bronce_antes = {p.name: sha(p) for p in (RAIZ / "data" / "bronce" / "inegi_defunciones").glob("*.csv")}

    # Limpieza: réplicas intercaladas (antes, después, antes, ...) para que el
    # calentamiento del disco o la caché no favorezca a una condición.
    for _ in range(REPLICAS_LIMPIEZA):
        filas.append(medir("limpieza", "antes", {"OPTIMIZACION_E3": "0"}))
        filas.append(medir("limpieza", "despues", {}))

    if "--sin-red" not in sys.argv:
        # Antes: descarga todo (y deja registrada la huella para el "después").
        filas.append(medir("captura", "antes", {"OPTIMIZACION_E3": "0"}))
        filas.append(medir("captura", "despues", {}))

    bronce_despues = {p.name: sha(p) for p in (RAIZ / "data" / "bronce" / "inegi_defunciones").glob("*.csv")}
    m = pd.DataFrame(filas)
    previas = SALIDA / "mediciones.csv"
    m.to_csv(previas, index=False)

    res = {"bronce_sin_cambios": bronce_antes == bronce_despues}
    for tarea, g in m.groupby("tarea"):
        a, d = g[g.condicion == "antes"], g[g.condicion == "despues"]
        res[tarea] = {
            "n_por_condicion": int(len(a)),
            "seg_antes": round(a["seg"].mean(), 3), "seg_despues": round(d["seg"].mean(), 3),
            "seg_de_antes": round(a["seg"].std(), 3) if len(a) > 1 else None,
            "seg_de_despues": round(d["seg"].std(), 3) if len(d) > 1 else None,
            "mejora_tiempo_pct": round((1 - d["seg"].mean() / a["seg"].mean()) * 100, 1),
            "mem_mb_antes": round(a["mem_mb"].mean(), 1), "mem_mb_despues": round(d["mem_mb"].mean(), 1),
            "mejora_memoria_pct": round((1 - d["mem_mb"].mean() / a["mem_mb"].mean()) * 100, 1),
            "mem_trabajo_mb_antes": round(a["mem_trabajo_mb"].mean(), 1),
            "mem_trabajo_mb_despues": round(d["mem_trabajo_mb"].mean(), 1),
            "errores_antes": int(a["errores"].sum()), "errores_despues": int(d["errores"].sum()),
            "detalle_antes": a["detalle"].iloc[0], "detalle_despues": d["detalle"].iloc[0],
        }
        if tarea == "limpieza":
            res[tarea]["salida_identica"] = bool(g["detalle"].nunique() == 1)
            from scipy import stats

            res[tarea]["welch_p_tiempo"] = float(stats.ttest_ind(a["seg"], d["seg"], equal_var=False).pvalue)
    (SALIDA / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    grafica(res)
    print(json.dumps(res, ensure_ascii=False, indent=2))


def grafica(res: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tareas = [t for t in ("captura", "limpieza") if t in res]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, (met, titulo) in zip(axs, [("seg", "Tiempo (s)"), ("mem_mb", "Memoria pico (MB)")], strict=True):
        x = range(len(tareas))
        antes = [res[t][f"{met}_antes"] for t in tareas]
        desp = [res[t][f"{met}_despues"] for t in tareas]
        ax.bar([i - 0.2 for i in x], antes, 0.38, label="Antes", color="#eb6834")
        ax.bar([i + 0.2 for i in x], desp, 0.38, label="Después", color="#2a78d6")
        for i, (a, d) in enumerate(zip(antes, desp, strict=True)):
            ax.text(i - 0.2, a, f"{a:g}", ha="center", va="bottom", fontsize=8)
            ax.text(i + 0.2, d, f"{d:g}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(list(x), ["Captura (6 años EDR)", "Limpieza (Plata defunciones)"][:len(tareas)]
                      if tareas[0] == "captura" else ["Limpieza (Plata defunciones)"])
        ax.set_title(titulo)
        ax.spines[["top", "right"]].set_visible(False)
    axs[0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(SALIDA / "comparacion.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--hijo":
        hijo(sys.argv[2])
    else:
        main()
