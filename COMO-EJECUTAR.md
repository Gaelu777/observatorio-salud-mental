# Cómo ejecutar el observatorio (guía rápida)

Todos los comandos se escriben en **PowerShell** dentro de la carpeta del proyecto:

```powershell
cd D:\observatorio-salud-mental
```

---

## 1. Instalar todo (solo la primera vez, o si cambia `requirements-dev.txt`)

```powershell
pip install -r requirements-dev.txt
```

Instala pandas, statsmodels, geopandas, Streamlit, pytest, ruff y pip-audit con las versiones exactas del proyecto.

---

## 2. Ver el tablero

```powershell
streamlit run tablero/app.py
```

- Se abre solo en el navegador. Si no se abre, entra a **http://localhost:8501**.
- Tiene 4 pestañas: Pronóstico · Oferta y necesidad · Mapa multivariado · Calidad del sistema.
- Para **apagarlo**, presiona `Ctrl + C` en la terminal.
- Si cambian los datos, recarga la página (F5).

---

## 3. Buscar secretos con gitleaks

**Instalarlo (solo una vez):**

```powershell
winget install gitleaks
```

Después de instalarlo, cierra y vuelve a abrir PowerShell.

**Correrlo:**

```powershell
gitleaks git . -v
```

- Si dice **`no leaks found`**, todo está bien: no hay contraseñas, tokens ni llaves en todo el historial.
- Si encuentra algo, **no lo borres sin más**: el secreto sigue en los commits viejos. Primero hay que revocar o cambiar esa llave, y luego avisar.
- En versiones viejas de gitleaks el comando es `gitleaks detect -v`.

> No es obligatorio correrlo en tu computadora: GitHub lo corre solo en cada push (job **"secretos"** del workflow **CI**).

---

## 4. Correr las pruebas

```powershell
pytest --cov
```

- Tarda unos 2 minutos. Corre todo el pipeline desde Bronce y comprueba que da exactamente lo mismo.
- Al final debe decir `16 passed` (o más) y la cobertura total (meta: al menos 60 %).
- Las pruebas **no dejan archivos cambiados**: respaldan los datos y los restauran.

Revisar el estilo del código (linter):

```powershell
ruff check src tests tablero
```

Debe decir `All checks passed!`.

Revisar vulnerabilidades de las dependencias:

```powershell
pip-audit -r requirements.txt
```

Debe decir `No known vulnerabilities found`.

---

## 5. Regenerar los datos y análisis a mano

Normalmente **no hace falta**, porque GitHub Actions lo hace solo cada día. Si lo quieres correr tú, el orden importa:

```powershell
python src/plata.py              # Bronce -> Plata (Puerta de Calidad + cuarentena)
python src/oro.py                # Plata -> Oro
python src/geoespacial.py        # mapas y consultorios con coordenadas
python src/verificar_linaje.py   # comprueba que todo Oro llega a Bronce
python src/pronostico.py         # E1: pronóstico (docs/E1/pronostico/)
python src/multivariado.py       # E3: PCA y MANOVA (docs/E3/multivariado/)
python src/diccionario_oro.py    # diccionario de datos de Oro
```

Otros análisis (tardan más, solo cuando haga falta):

```powershell
python src/experimento_factorial.py   # E2: experimento 2^3 (unos minutos)
python src/optimizacion.py            # E3: mide antes vs después (unos 5 min, descarga del INEGI)
python src/optimizacion.py --sin-red  # solo la parte que no usa internet
```

---

## 6. GitHub Actions: qué es y cómo usarlo

Está en la pestaña **Actions** del repositorio en GitHub. Hay dos workflows:

| Workflow | Qué hace | Cuándo corre |
|---|---|---|
| **Pipeline Bronce-Plata-Oro** | Descarga los datos del INEGI, limpia, analiza y sube los datos nuevos | Solo, cada día a las 7:00 (hora de Colima). También a mano |
| **CI** | Revisa que nada se rompa: ruff, pruebas, pip-audit y gitleaks | En cada push |

**Para correrlo a mano:**
1. Entra a Actions.
2. Elige **Pipeline Bronce-Plata-Oro**.
3. Presiona el botón **"Run workflow"**.

> ⚠️ **No uses "Re-run"** en una corrida vieja: repite el código de ese día y puede fallar al subir los datos, como pasó el 2026-11-23.

**Si sale un tache rojo:** entra a la corrida y abre el paso que tiene el tache para leer el error.

---

## 7. Subir cambios con una rama (recomendado)

```powershell
git switch -c nombre-de-la-rama          # crea la rama y te cambia a ella
git add .
git commit -m "mensaje corto de lo que cambió"
git push -u origin nombre-de-la-rama     # sube la rama; la CI corre sola
```

1. Espera a que **CI** salga en verde en GitHub (pestaña Actions).
2. Luego pasa los cambios a `main`:

```powershell
git switch main
git pull                                 # trae lo que subió el robot del pipeline
git merge nombre-de-la-rama
git push
```

Para ver en qué rama estás y qué archivos cambiaron:

```powershell
git status
```

---

## 8. Marcar una entrega (tag)

```powershell
git tag e3
git push origin e3
```

Se hace **una sola vez por entrega** y cuando todo esté listo. Los profesores revisan el repositorio en el estado de ese tag.

Si ya existe un tag y hay que moverlo, **pregunta primero al profesor**.
