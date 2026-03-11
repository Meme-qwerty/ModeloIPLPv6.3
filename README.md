# IPLP CEN v6.3

Pipeline de conversión de datos para el modelo de **Planificación de Largo Plazo (PLP)** del Coordinador Eléctrico Nacional (CEN) de Chile.

Transforma el archivo maestro Excel (`.xlsm`) del caso IPLP en los archivos `.dat` de entrada requeridos por el solver PLP para la optimización del despacho hidrotérmico de largo plazo.

---

## Descripción general

El flujo de trabajo sigue tres etapas principales:

```
Excel (.xlsm)
    │
    ▼
parse_from_excel_to_dict()   ← lee ~30 hojas en diccionarios anidados
    │
    ▼
dicts_to_dfs()               ← convierte diccionarios → DataFrames de pandas
    │
    ▼
write_dat_files()            ← genera ~24 archivos .dat especializados
    │
    ▼
ArchivosDat/*.dat  +  indhor.csv
```

---

## Requisitos

- Python 3.8+
- pandas
- numpy
- openpyxl
- jinja2
- scipy
- scikit-learn
- holidays

Instalar dependencias:
```bash
pip install pandas numpy openpyxl jinja2 scipy scikit-learn holidays
```

---

## Uso

```bash
python main.py --casoIPLP IPLP20251107_cen_v6.3.xlsm
```

Los archivos de salida se generan en la carpeta `ArchivosDat/`.

---

## Estructura del proyecto

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada CLI; define flags de simulación (`opts_dict`); orquesta el pipeline |
| `main_functions.py` | Funciones de alto nivel del pipeline: `parse_from_excel_to_dict`, `dicts_to_dfs`, `write_dat_files`; agregación de demanda por bloques |
| `data_parsers.py` | Limpieza y transformación de datos por hoja: etapas, bloques, centrales, afluentes (modelo estocástico log-normal), costos, mantenimientos, demanda |
| `dict_creators.py` | Una función por archivo `.dat` de salida; convierte DataFrames procesados en diccionarios estructurados para el templating |
| `templates_dat.py` | Plantillas Jinja2 con formato preciso de columnas para cada archivo `.dat` |
| `utils.py` | Enumeraciones (`TipoSimulacion`, `TipoAleatorio`), renderizado Jinja2, escritura de `indhor.csv`, tabla horaria completa |
| `func_cdec.py` | Clase `Embalses` con ecuaciones hidráulicas (polinomiales/tabla) para ~15 embalses chilenos: cotas, volúmenes, rendimientos |
| `contenedores_auxiliares.py` | Configuración estática: mapeo de hojas Excel, renombrado de columnas, calendarios hidrológicos, configuración de bloques |

---

## Archivos de entrada

**Archivo principal:** `IPLP20251107_cen_v6.3.xlsm`

Hojas relevantes leídas del Excel:

| Hoja | Contenido |
|---|---|
| `Etapas` | Definición de etapas (año, mes, horas, factor descuento, N° bloques) |
| `Consumo` / `Demanda-R/L/LD` | Demanda eléctrica por barra y bloque |
| `Caudales_Ah1/Ah2` | Series de caudales afluentes (modelo estocástico) |
| `Caudales_historicos` | Hidrología histórica |
| `Hidrología` | Parámetros del modelo hidrológico |
| `Barras` | Definición de barras eléctricas |
| `Líneas` | Configuración de líneas de transmisión |
| `Centrales` | Unidades generadoras (embalses, pasadas, térmicas) |
| `CV_MP` | Costos variables por central |
| `MantLIN` / `MantEMB` / `MantEMBh` | Mantenimientos de líneas y embalses |
| `Baterias` | Unidades de almacenamiento (baterías) |
| `MAULEN` / `LAJAM` | Derechos de agua ríos Maule y Laja |
| `Rebalse` / `Extracciones` / `Filtraciones` | Curvas hidráulicas especiales |
| `Rendimiento` | Curvas de rendimiento de embalses |
| `CENPMAX` | Curvas Pmax vs. volumen |
| `Datos` | Flags de configuración de la simulación |
| `C.Iniciales(1)` – `ERNC(6)` | Condiciones iniciales y ERNC |

---

## Archivos de salida (`ArchivosDat/`)

| Archivo | Contenido |
|---|---|
| `plpeta.dat` | Definición de etapas (año, mes, horas, descuento) |
| `plpblo.dat` | Definición de bloques horarios |
| `plpbar.dat` | Nombres de barras eléctricas |
| `plpcnfli.dat` | Configuración de líneas (R, X, límites de flujo) |
| `plpcnfce.dat` | Configuración de unidades generadoras |
| `plpidsim.dat` | Índice de simulación hidrológica por etapa |
| `plpidape.dat` / `plpidap2.dat` | Índices de apertura hidrológica |
| `plpaflce.dat` | Series estocásticas de afluentes por etapa |
| `plpcosce.dat` | Costos variables de centrales térmicas por etapa |
| `plpmanem.dat` | Límites de volumen de embalses por etapa |
| `plpminembh.dat` | Volumen mínimo de embalses con costo slack |
| `plpmanli.dat` | Ventanas de mantenimiento de líneas |
| `plpmancen.dat` | Mantenimiento de capacidad de centrales (potmin/potmax) |
| `plpdem.dat` | Demanda por barra y bloque |
| `plpextrac.dat` | Puntos de extracción de agua |
| `plpcenre.dat` | Curvas de rendimiento de embalses |
| `plpvrebemb.dat` | Volúmenes de rebalse por embalse |
| `plpfilemb.dat` | Curvas de filtración por embalse |
| `plpcenpmax.dat` | Curvas Pmax–volumen |
| `plpplem1.dat` | Datos cota/volumen para PLPEM1 |
| `plpcenbat.dat` | Configuración de unidades de batería |
| `plplajam.dat` | Acuerdo de derechos de agua lago Laja |
| `plpmaulen.dat` | Acuerdo de derechos de agua río Maule |
| `indhor.csv` | Mapeo horario-bloque (año/mes/día/hora/bloque) |

---

## Configuración

### Flags de simulación (`opts_dict` en `main.py`)

| Flag | Valor por defecto | Descripción |
|---|---|---|
| `SIM0` | `NOCONDICIONADA4s` | Tipo de simulación hidrológica |
| `APE0` | `ALEATORIO_ANO_CON` | Tipo de muestreo aleatorio anual |
| `AUX0` | `SIM_HISTORICA` | Usar hidrología histórica |
| `UANO` | `True` | Usar sólo los años más recientes |
| `HIDE` | `False` | Ocultar generadores especiales |
| `NAPEF` | `False` | Modo NAPEF |
| `CDEC` | `False` | Modo CEN (omite extracción/rendimiento/rebalse/filtración/cenpmax) |
| `AFL4` | `False` | Generar afluentes deterministas a 4 semanas |

### Configuración de bloques (`BLOQUES_CONFIG` en `contenedores_auxiliares.py`)

```python
{3: [8, 8, 8], 5: [6, 3, 8, 3, 4], 10: [3, 2, 3, 2, 2, 3, 2, 3, 2, 2]}
```

Mapea el número de bloques por etapa a la lista de horas por bloque (suma = 24). El número de bloques se lee dinámicamente desde la columna `Nº Bloques` de la hoja `Etapas`.

### Convención del año hidrológico

Abril = mes 1 ... Marzo = mes 12 (implementado en `HIMONTH` / `MES_MESC`).

---

## Embalses soportados (`func_cdec.py`)

La clase `Embalses` implementa ecuaciones hidráulicas (cotas, volúmenes, rendimientos) para los siguientes embalses chilenos:

Guaiquivilo, Cipreses, Laja, Maule, Colbún, Ralco, Rapel, El Toro, Angostura, Pangue, Pehuenche, Canutillar, Pilmaiquén.
