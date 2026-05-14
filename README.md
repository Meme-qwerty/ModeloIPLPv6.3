# PLPv6.3 - Sistema de Generación de Archivos .DAT para Simulación de Sistemas Eléctricos

## Descripción General

**PLPv6.3** es un proyecto Python que convierte datos de planificación de sistemas eléctricos (originarios de archivos Excel) en un conjunto de archivos `.dat` que sirven como entrada para simuladores de despacho y planeamiento de operación.

El proyecto emula la lógica de la **Macro PLP** (desarrollada originalmente en VBA) para procesar información de:
- Etapas y bloques de tiempo
- Configuración de barras y líneas
- Centrales de generación (hidroeléctricas, térmicas, ERNC, baterías)
- Demanda y consumo por sector
- Hidrologías (caudales históricos y estocásticos)
- Restricciones especiales (Laja, Maule)
- Mantenimientos y operación

---

## Estructura del Proyecto

```
PLPv6.3/
├── main.py                    # Punto de entrada principal
├── main_functions.py          # Funciones de flujo principal (Excel → dict → dataframes → .dat)
├── data_parsers.py            # Parseo de datos desde Excel a formatos internos
├── dict_creators.py           # Creación de diccionarios para plantillas .dat
├── utils.py                   # Funciones utilitarias (cálculos, formateo)
├── templates_dat.py           # Plantillas Jinja2 para generación de archivos .dat
├── func_cdec.py               # Cálculos específicos para embalses (cotas, volúmenes)
├── macro_profiles.py          # Perfiles de macros (compatibilidad de versiones)
├── scan_macros.py             # Escaneo de archivos de macro VBA
├── contenedores_auxiliares.py # Contenedores de datos (diccionarios, etiquetas)
├── compare_all.py             # Comparación de archivos generados con referencia
├── IPLP20260407_a.xlsm        # Archivo Excel de entrada (caso de prueba)
├── resultados_comparacion.txt # Resultados de comparaciones
├── ArchivosDat/               # Directorio de salida de archivos .dat
│   ├── indhor.csv             # Índice horario
│   └── *.dat                  # Archivos generados (.dat)
├── Base_Prueba_v6.3/          # Base de referencia para pruebas
│   ├── FUNCCDEC.xla
│   ├── MacroPLP_I_20250508.xla
│   ├── indhor.csv
│   └── plpfal.prn
├── macros/                    # Macros VBA de referencia
│   └── MacroPLP_I_20250508.xla
└── .ipynb_checkpoints/        # Caché de Jupyter (ignorar)
```

---

## Módulos Python

### **main.py**
Punto de entrada principal con interfaz de línea de comandos.

**Funcionalidades:**
- Selección interactiva de archivos Excel
- Selección interactiva de perfiles de macro
- Argumentos CLI para procesamiento automatizado

**Uso:**
```bash
# Interactivo
python main.py

# Especificando archivo y macro
python main.py --casoIPLP IPLP20260407_a.xlsm --macro MacroPLP_I_20250508

# Generando solo ciertos archivos
python main.py --casoIPLP caso.xlsm --files plpeta.dat plpbar.dat plpcnfce.dat
```

---

### **main_functions.py**
Orquesta el flujo principal de procesamiento.

**Funciones principales:**
- `parse_from_excel_to_dict()`: Lee Excel → convierte a diccionario JSON-compatible
- `dicts_to_dfs()`: Convierte diccionarios a DataFrames de Pandas
- `write_dat_files()`: Genera archivos .dat desde DataFrames

**Características especiales:**
- Detección automática de hojas nuevas en Excel
- Inferencia de headers y columnas relevantes
- Soporte para filtrado selectivo de archivos a generar

---

### **data_parsers.py**
Parsea datos desde DataFrames de Excel a formatos internos.

**Funciones principales:**
| Función | Descripción |
|---------|------------|
| `parse_etapas()` | Procesa tabla de etapas: fechas → años hidrológicos, horas, semanas |
| `parse_bloques()` | Crea índice de bloques dentro de etapas |
| `parse_barras()` | Extrae definición de barras eléctricas |
| `parse_lineas()` | Parsea líneas de transmisión (resistencia, reactancia, pérdidas) |
| `parse_centrales()` | Empalmes complejos: embalses, térmicas, pasadas, baterías, fallas |
| `parse_afluentes()` | Procesa series de caudales (históricos y estocásticos) |
| `parse_filtraciones()` | Relaciones volumen-filtración en embalses |
| `parse_rendimientos()` | Curvas rendimiento vs cota de embalses |
| `parse_baterias()` | Configuración de sistemas de almacenamiento |
| `parse_cenpmax()` | Potencia máxima en función del volumen del embalse |

---

### **dict_creators.py**
Genera diccionarios estructurados desde DataFrames para plantillas.

**Funciones principales (por archivo .dat):**

| Archivo .dat | Función | Datos Generados |
|--------------|---------|-----------------|
| plpeta.dat | `get_etapas_dict()` | Duración de etapas, meses, años |
| plpblo.dat | `get_bloques_dict()` | Bloques dentro de cada etapa |
| plpbar.dat | `get_barras_dict()` | Nombres y números de barras |
| plpcnfli.dat | `get_lineas_dict()` | Config. de líneas (resistencia, reactancia) |
| plpcnfce.dat | `get_cnfcen_dict()` | Config. de centrales generadoras |
| plpidsim.dat | `get_simape_dict()` | Semillas y números aleatorios para simulación |
| plpaflce.dat | `get_aflce_dict()` | Afluentes (caudales) por central |
| plpmanem.dat | `get_manem_dict()` | Mantenimientos de embalses |
| plpmanli.dat | `get_manli_dict()` | Mantenimientos de líneas |
| plpcosce.dat | `get_cosce_dict()` | Costos variables y mantenimiento de centrales |
| plpdem.dat | `get_demanda_dict()` | Demanda por barra, hora, tipo de día |
| plpmancen.dat | `get_mant_dict2()` | Mantenimientos de centrales |
| plpplem1.dat | `get_plem1_dict()` | Embalses con curva cota-volumen |
| plpcenbat.dat | `get_cenbat_dict()` | Baterías de almacenamiento |
| plplajam.dat | `get_lajam_dict()` | Convenio de riego Laja (especial) |
| plpmaulen.dat | `get_maulen_dict()` | Convenio de riego Maule (especial) |

---

### **utils.py**
Funciones utilitarias compartidas.

**Funciones principales:**
- `ArregloNumAleat()`: Generación de números aleatorios/pseudoaleatorios para simulación
- `process_blodem()`: Procesamiento de demanda por bloque
- `apply_proyectos()`: Incorporación de proyectos industriales en demanda
- `get_full_etapas()`: Expansión horaria de etapas con información de feriados
- `correccion_preredondeo()`: Redondeo controlado de valores numéricos

**Enums:**
- `TipoSimulacion`: Tipos de simulación (CONDICIONADA/NOCONDICIONADA/PROGMENSUAL)
- `TipoAleatorio`: Métodos de selección estocástica
- `TipoSimulacion2`: Histórica vs. Aleatoria

---

### **templates_dat.py**
Plantillas Jinja2 para generar archivos .dat.

Define templates formateados (como strings Jinja2) para:
- **Etapas, Bloques, Barras, Líneas**: Datos de configuración base
- **Centrales, Embalses, Baterías**: Configuración de generación
- **Demanda**: Curvas de demanda por barra
- **Laja y Maule**: Archivos especiales de restricciones de riego
- **Mantenimientos**: Planes de mantenimiento
- **Afluentes**: Series de caudales

Ejemplo de template (ETA_TMPL):
```jinja2
# Archivo con la duracion de las etapas
{{ "{:8d}".format(etapas.NETAPAS) }}   'H'
# Año  Mes  Etapa FDesh   NHoras    FactTasa    TipoEtapa
{% for año, mes, eta, fde, nho, fta, teta in etapas.DATA -%}
{{ "{:2s}".format(" ") }}{{ "{:03d}".format(año) }}  {{ "{:03d}".format(mes) }} ...
```

---

### **func_cdec.py**
Cálculos específicos de embalses chilenos usando interpolación polinómica.

**Clase principal: `Embalses`**

Métodos principales:
- `cota(nombre, volumen)`: Convierte volumen → cota (altura)
- `volumen(nombre, cota)`: Convierte cota → volumen
- `dvol(nombre, cota)`: Derivada de volumen respecto a cota
- `rendimiento(nombre, cota)`: Rendimiento en MWh/m³ vs cota

**Embalses soportados:**
- Guaiquivilo, Cipreses, Lleuques, Canutillar, Rucatayo
- Pilmaiquén, Pangue, Pehuenche, Angostura, El Toro
- Laja, Machicura, Pólcura, Rapel, Ralco, Colbún

Usa interpolación polinómica (grados 2-3), tablas de datos y métodos iterativos de Newton-Raphson.

---

### **macro_profiles.py**
Gestión de perfiles de macros para compatibilidad de versiones.

**Clase: `MacroProfile`**
```python
@dataclass
class MacroProfile:
    name: str                    # ID único
    display_name: str            # Nombre descriptivo
    has_extra_tags: bool         # Si genera etiquetas extra
    cost_precision: int          # Decimales en costos
    skip_stages_offset: int      # Offset de etapas
```

**Perfiles registrados:**
- `MacroPLP_I_20220414`: Versión v5.0 (antigua, tiene desplazamiento de 4 etapas)
- `MacroPLP_I_20250508`: Versión v6.3 (actual, con etiquetas extra)

---

### **scan_macros.py**
Herramienta para escanear archivos de macro VBA.

Detecta:
- Presencia de etiquetas extra (`FV, EO, CS`)
- Referencias a tipos de etapas
- Codificación y estructura interna

---

### **contenedores_auxiliares.py**
Contenedores de datos globales y configuraciones.

**Diccionarios principales:**

| Variable | Contenido |
|----------|-----------|
| `EXCEL_DICT` | Mapeo de nombres de hojas Excel → configuración (header, usecols) |
| `TAGS_LAJA` | Definición de parámetros del Convenio Laja (52 entradas) |
| `TAGS_MAULE` | Definición de parámetros del Convenio Maule (54 entradas) |
| `CHG_COL_NAME` | Renombramiento de columnas de centrales |
| `HIMONTH` / `IMONTH` | Mapeo mes calendario ↔ mes hidrológico |
| `BLOQUES_CONFIG` | Distribución de horas por tipo de bloque |
| `MES_MESC` / `MESC_MES` | Conversiones de mes calendar/hidrológico |

---

### **compare_all.py**
Herramienta de validación y comparación.

Compara archivos .dat generados con un directorio de referencia:
```bash
python compare_all.py ArchivosDat/ Base_Prueba_v6.3/
```

Reporta:
- IGUAL: archivos idénticos
- DIFERENTE: diferencias de contenido o tamaño
- NO EXISTE: archivos no generados

---

## Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LECTURA EXCEL (parse_from_excel_to_dict)                    │
│    - Lee según EXCEL_DICT                                      │
│    - Detecta hojas nuevas                                      │
│    - Convierte a diccionario JSON-compatible                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CONVERSIÓN A DATAFRAMES (dicts_to_dfs)                      │
│    - Diccionario → DataFrames de Pandas                        │
│    - Indexado y ordenado                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. PROCESAMIENTO DE DEMANDA (process_blodem)                   │
│    - Interpola demanda horaria                                 │
│    - Ajusta por feriados                                       │
│    - Aplica proyectos industriales                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. PARSEO DE DATOS (data_parsers)                              │
│    - parse_etapas() → años hidro, semanas                      │
│    - parse_centrales() → embalses, térmicas, etc.              │
│    - parse_afluentes() → caudales históricos/estocásticos      │
│    - ... (otros datos)                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. CREACIÓN DE DICCIONARIOS (dict_creators)                    │
│    - get_etapas_dict()   → {NETAPAS, DATA}                     │
│    - get_cnfcen_dict()   → {NCEN, NEMB, SERIES, ...}           │
│    - get_aflce_dict()    → {NCAU, NHIDRO, MESETA, ...}         │
│    - ... (otros diccionarios)                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. GENERACIÓN DE ARCHIVOS .DAT (write_dat_files)               │
│    - Renderiza plantillas Jinja2                               │
│    - Escribe archivos .dat en formato texto                    │
│    - Genera indhor.csv                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Archivos .DAT Generados

### Archivos Estructurales
| Archivo | Descripción | Líneas Típicas |
|---------|------------|-----------------|
| `plpeta.dat` | Duración y características de etapas | 50-200 |
| `plpblo.dat` | Definición de bloques | 500-5000 |
| `plpbar.dat` | Definición de barras eléctricas | 20-100 |
| `plpcnfli.dat` | Líneas de transmisión | 100-500 |

### Archivos de Centrales
| Archivo | Descripción |
|---------|------------|
| `plpcnfce.dat` | Configuración de centrales (generadores, embalses, baterías) |
| `plpplem1.dat` | Embalses con relación cota-volumen |

### Archivos de Operación
| Archivo | Descripción |
|---------|------------|
| `plpidsim.dat` | Números aleatorios para simulación Monte Carlo |
| `plpidape.dat` | Índices de años para aperturas condicionadas |
| `plpaflce.dat` | Afluentes (caudales) por central y etapa |
| `plpdem.dat` | Demanda por barra, bloque y tipo de día |

### Archivos de Mantenimiento
| Archivo | Descripción |
|---------|------------|
| `plpmanem.dat` | Mantenimiento de embalses |
| `plpmanli.dat` | Mantenimiento de líneas |
| `plpmancen.dat` | Mantenimiento y paradas de centrales |

### Archivos Especiales
| Archivo | Descripción |
|---------|------------|
| `plplajam.dat` | Convenio de riego Laja (52 parámetros) |
| `plpmaulen.dat` | Convenio de riego Maule (54 parámetros) |
| `plpcenbat.dat` | Baterías de almacenamiento |
| `indhor.csv` | Índice horario (referencia de bloques a horas reales) |

---

## Configuración de Entrada (EXCEL_DICT)

El proyecto espera un Excel con las siguientes hojas (nombre y header específico):

| Hoja | Header | Columnas Usadas | Obligatorio |
|------|--------|-----------------|------------|
| Etapas | 3 | A:Q | ✓ |
| Consumo | 3 | A:I | ✓ |
| Demanda-R | 5 | A:AX | ✓ |
| Demanda-L | 5 | A:AX | ✓ |
| Demanda-LD | 5 | A:AX | ✓ |
| Barras | 4 | A:B | ✓ |
| Líneas | 4 | A:N | ✓ |
| Centrales | 4 | A:AS | ✓ |
| Hidrología | 0 | B:D | ✓ |
| Caudales_Ah1 | 4 | A:BE | ✓ |
| Caudales_Ah2 | 4 | A:BE | ✓ |
| Caudales_historicos | 4 | A:BE | ✓ |
| CVariable/CV_MP | 4 | A:E | ✓ |
| MantEMB | 4 | A:F | Opcional |
| LAJAM | 3 | C:Q | Opcional |
| MAULEN | 3 | C:Q | Opcional |
| Baterias | 5 | A:K | Opcional |
| Rebalse | 0 | A:C | Opcional |
| Extracciones | 0 | A:C | Opcional |
| Filtraciones | 0 | A:H | Opcional |
| Rendimiento | 0 | A:F | Opcional |
| CENPMAX | 0 | A:G | Opcional |

Las nuevas hojas se detectan automáticamente y se agregan a `contenedores_auxiliares.py`.

---

## Opciones de Ejecución

### Opciones de Simulación (`opts_dict`)

```python
opts_dict = {
    'SIM0': TipoSimulacion.NOCONDICIONADA4s,  # Tipo de simulación
    'APE0': TipoAleatorio.ALEATORIO_ANO_CON,  # Método de apertura
    'AUX0': TipoSimulacion2.SIM_HISTORICA,    # Simulación histórica
    'UANO': True,                              # Usar año anterior
    'HIDE': False,                             # Ocultar datos
    'NAPEF': False,                            # Sin apertura frecuencial
    'CDEC': False,                             # Incluir CDEC
    'AFL4': False,                             # Afluentes de 4 semanas
    'macro_profile': profile                   # Perfil de macro
}
```

### Generación Selectiva

Solo generar ciertos archivos:
```bash
python main.py --casoIPLP caso.xlsm --files plpeta.dat plpblo.dat
```

---

## Correcciones y Características Especiales

### Interpolación de Volúmenes en Embalses (func_cdec.py)
Si faltan datos de volumen o rendimiento, se interpola automáticamente usando tablas cota-volumen de cada embalse específico (Colbún, Maule, Angostura, etc.).

### Ajuste de Baterías (dict_creators.py)
Corrección especial: `BAT_MARIA_ELENA_FV` (índice 29) asigna barra 76 (no 75).

### Redondeo Pre-renderizado
Valores numéricos se redondean controladamente antes de renderizar:
- Potencias, costos, afluentes: 1 decimal
- Rendimientos: 3 decimales
- Volúmenes: 7 decimales (opcional)

### Manejo de Proyectos Industriales
Incorpora cambios de demanda por proyectos con duración especificada, ponderando por horas de traslape en cada bloque.

### Detección de Feriados
Ajusta clasificación de día (LU, TR, SA, DO) según tabla de feriados en Excel.

---

## Compatibilidad de Versiones

El proyecto soporta múltiples versiones de macros través de `MacroProfile`:

- **v5.0 (20220414)**: Con desplazamiento de etapas (+4), sin etiquetas extra
- **v6.3 (20250508)**: Actual, con etiquetas extra FV, EO, CS

Se pueden agregar nuevos perfiles registrando en `MACRO_REGISTRY` en `macro_profiles.py`.

---

## Dependencias

```
pandas>=1.3
numpy>=1.21
scipy>=1.7
scikit-learn>=1.0
jinja2>=3.0
python-holidays>=0.12
openpyxl>=3.6
```

---

## Instalación

```bash
# Clonar o descargar el proyecto
cd PLPv6.3

# Instalar dependencias (opcional, si no las tiene)
pip install -r requirements.txt  # si existe

# O instalarlas manualmente:
pip install pandas numpy scipy scikit-learn jinja2 python-holidays openpyxl
```

---

## Uso Rápido

### 1. Procesamiento Interactivo
```bash
python main.py
# → Selecciona archivo Excel
# → Selecciona macro
# → Genera archivos en ArchivosDat/
```

### 2. Procesamiento Automatizado
```bash
python main.py --casoIPLP IPLP20260407_a.xlsm --macro MacroPLP_I_20250508
```

### 3. Generar Solo Algunos Archivos
```bash
python main.py --casoIPLP caso.xlsm --files plpeta.dat plpbar.dat
```

### 4. Validar Archivos Generados
```bash
python compare_all.py ArchivosDat/ Base_Prueba_v6.3/
```

---

## Estructura de Salida

```
ArchivosDat/
├── plpeta.dat      # Etapas
├── plpblo.dat      # Bloques
├── plpbar.dat      # Barras
├── plpcnfli.dat    # Líneas
├── plpcnfce.dat    # Centrales
├── plpidsim.dat    # Simulación
├── plpidape.dat    # Aperturas
├── plpaflce.dat    # Afluentes
├── plpdem.dat      # Demanda
├── plpmanem.dat    # Mant. embalses
├── plpmanli.dat    # Mant. líneas
├── plpmancen.dat   # Mant. centrales
├── plplajam.dat    # Laja
├── plpmaulen.dat   # Maule
├── plpcenbat.dat   # Baterías
└── indhor.csv      # Índice horario
```

---

## Notas de Desarrollo

### Años Hidrológicos
El sistema ajusta años calendario a años hidrológicos (abril-marzo) automáticamente. La semana 1 del año hidrológico se calcula desde la semana inicial especificada.

### Mes Hidrológico
Conversión: Enero (1) → Octubre (10), ..., Marzo (3) → Diciembre (12).

### Cambios Recientes (2026)
- **Marzo 2026**: Soporte para baterías, lectura de bloques desde Excel
- **Abril 2026**: Espaciamiento mejorado en plpblo.dat, soporte para Proyectos
- **Mayo 2026**: Compatibilidad JSON mejorada

---

## Troubleshooting

### Error: "No se encontraron archivos Excel"
→ Asegúrese de ejecutar desde el directorio con .xlsm

### Error: "No se encontró la hoja 'Etapas'"
→ Verifique nombres de hojas en Excel según EXCEL_DICT

### Archivos .dat vacíos o incompletos
→ Revise si hay datos faltantes en las hojas Excel requeridas

### Diferencias con referencia en compare_all.py
→ Puede deberse a cambios intencionales de versión o correcciones aplicadas

---

## Autor
Desarrollado para el sistema eléctrico chileno (PLP - Planificación de Largo Plazo).

## Versión
**v6.3** (Mayo 2026)

## Licencia
[Especifique según su política]

---

## Contacto / Soporte
Para reportar problemas o sugerencias, consulte con el equipo de desarrollo.
