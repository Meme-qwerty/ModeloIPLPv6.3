import pandas as pd  
import numpy as np   
import os            
import sys           
import warnings      

from contenedores_auxiliares import EXCEL_DICT, CEN_COLS, BLOQUES_CONFIG  
from templates_dat import *   
from dict_creators import *   
from utils import *           

#DETECCIÓN AUTOMÁTICA DE HOJAS NUEVAS Y FALTANTES
def _inferir_header(df_raw: pd.DataFrame) -> int:
    for i, row in df_raw.head(10).iterrows():
        valores = row.dropna()
        if len(valores) == 0:
            continue
        n_strings = sum(isinstance(v, str) for v in valores)
        if n_strings / len(valores) >= 0.6:
            return int(i)
    return 0    

def _inferir_usercols(df: pd.DataFrame) -> str:
    df_limpio = df.dropna(axis=1, how='all')
    n_cols = len(df_limpio.columns)
    if n_cols == 0:
        return "A:A"
    def col_a_letra(n: int) -> str:
        resultado = ""
        while n > 0:
            n, resto = divmod(n - 1, 26)
            resultado = chr(65 + resto) + resultado
        return resultado
    return f"A:{col_a_letra(n_cols)}"

def _leer_hoja_automatica(xls: pd.ExcelFile, sheet_name: str) -> tuple[pd.DataFrame, int, str]:
    df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    header_inferido = _inferir_header(df_raw)
    df = pd.read_excel(xls, sheet_name=sheet_name, header=header_inferido)
    usecols_inferido = _inferir_usercols(df)
    df_final = pd.read_excel(xls, sheet_name=sheet_name, header=header_inferido, usecols=usecols_inferido)
    return df_final, header_inferido, usecols_inferido

def _agregar_hojas_a_excel_dict(hojas_nuevas_info: list[dict]) -> None:
    dir_script = os.path.dirname(os.path.abspath(__file__))
    ruta_aux = os.path.join(dir_script, "Contenedores_auxiliares.py")
    if not os.path.isfile(ruta_aux):
        print(f"No se encontro contedores auxiliares.py en {dir_script}")
        return
    with open(ruta_aux, "r", encoding="utf-8") as f:
        contenido = f.read()
    lineas_nuevas = []
    for info in hojas_nuevas_info:
        clave = info["clave_dict"]
        sheet_name = info["sheet_name"]
        header = info["header"]
        usecols = info["usecols"]

        if f'"{clave}"' in contenido or f"'{clave}'" in contenido:
            print(f" i '{clave}' ya existe en el Excel_dict, se omite")
            continue
        linea = (
            f'          "{clave}":{{"sheet_name":"{sheet_name}", '
            f'"header":{header}, "usecols":"{usecols}"}},  '
            f'# agregado automaticamente\n'
        )
        lineas_nuevas.append(linea)
    if not lineas_nuevas:
        return
    
    MARCADOR = "### mapeo mes"
    if MARCADOR not in contenido:
        print(f"No se encontro el marcador de fin de excel_dict")
        print(f" Agregue manualmente a excel_dict")
        for l in lineas_nuevas:
            print(f" {l.strip()}")
    idx_marcador = contenido.index(MARCADOR)
    bloque_antes = contenido[:idx_marcador]
    idx_cierre = bloque_antes.rfind("}")
    if idx_cierre == -1:
        print(f"No se pudo localizar el cierre de excel_dict")
        return
    contenido_nuevo = contenido[:idx_cierre] + "".join(lineas_nuevas) + contenido[idx_cierre:]

    with open(ruta_aux, "w", encoding="utf-8") as f:
        f.write(contenido_nuevo)

    print(f"  ✓ EXCEL_DICT actualizado en contenedores_auxiliares.py")
    print(f"    Claves agregadas: {[i['clave_dict'] for i in hojas_nuevas_info]}")
    print(f"    Revise el archivo si desea ajustar header o usecols manualmente.")

def _resolver_hoja(sheet_name_config, hojas_disponibles: set) -> str:
    if isinstance(sheet_name_config, list):
        for nombre in sheet_name_config:
            if nombre in hojas_disponibles:
                return nombre
        return sheet_name_config[0]  
    return sheet_name_config  

#función que lee un archivo Excel y lo convierte en un diccionario de diccionarios
def parse_from_excel_to_dict(path_to_excel: str) -> dict:
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
    pexcel = os.path.normpath(path_to_excel)
    if not os.path.isfile(pexcel):
        raise FileNotFoundError(f" No se encuentra el archivo {pexcel} en la ruta indicada")
    dict_from_excel = {}
    xls = pd.ExcelFile(pexcel)
    hojas_en_excel     = xls.sheet_names
    hojas_en_excel_set = set(hojas_en_excel)
    sheeets = []
    usecols = []
    headers = []
    kkeys   = []
    for name, dd in EXCEL_DICT.items():
        nombre_resuelto = _resolver_hoja(dd['sheet_name'], hojas_en_excel_set)
        sheeets.append(nombre_resuelto)
        usecols.append(dd['usecols'])
        headers.append(dd['header'])
        kkeys.append(name)
    hojas_faltantes = [
        (k, ws, EXCEL_DICT[k]['sheet_name'])
        for k, ws in zip(kkeys, sheeets)
        if ws not in hojas_en_excel_set
    ]

    if hojas_faltantes:
        pass
    else:
        pass

    for ws, c, h, k in zip(sheeets, usecols, headers, kkeys):
        try:
            print(f"  Leyendo hoja: {ws}")
            df_test = pd.read_excel(xls, sheet_name=ws, usecols=c, header=h)
            df_test.name = k
            dict_from_excel[k] = df_test.convert_dtypes().to_dict()
        except Exception:
            df_test = pd.DataFrame()
            df_test.name = k
            dict_from_excel[k] = df_test.convert_dtypes().to_dict()
            continue
    hojas_conocidas = set(sheeets)
    hojas_nuevas    = [h for h in hojas_en_excel if h not in hojas_conocidas]

    if hojas_nuevas:
        # print(f"\n{'='*60}")
        # print(f" Se detectaron {len(hojas_nuevas)} hojas nuevas en el Excel:")
        # for hn in hojas_nuevas:
        #     print(f"     • {hn}")
        # print(f"{'='*60}")
        # print(" Leyendo hojas nuevas con configuración automática\n")
        hojas_nuevas_info = []

        for hoja_nueva in hojas_nuevas:
            try:
                # print(f"  Procesando hoja nueva: '{hoja_nueva}'")
                df_nuevo, header_inf, usecols_inf = _leer_hoja_automatica(xls, hoja_nueva)
                clave = hoja_nueva.strip().replace(" ", "_")
                df_nuevo.name = clave
                dict_from_excel[clave] = df_nuevo.convert_dtypes().to_dict()
                # print(f"    Si '{hoja_nueva}' leída: {len(df_nuevo)} filas × {len(df_nuevo.columns)} columnas")
                # print(f"      header inferido={header_inf}, usecols inferido='{usecols_inf}'")
                # print(f"      columnas: {list(df_nuevo.columns)}")

                hojas_nuevas_info.append({
                    "sheet_name": hoja_nueva,
                    "clave_dict": clave,
                    "header":     header_inf,
                    "usecols":    usecols_inf,
                    "n_filas":    len(df_nuevo),
                    "n_columnas": len(df_nuevo.columns),
                    "columnas":   [str(c) for c in df_nuevo.columns],
                })

            except Exception as e:
                # print(f" No se pudo leer '{hoja_nueva}': {type(e).__name__}: {e}")
                clave = hoja_nueva.strip().replace(" ", "_")
                df_vacio = pd.DataFrame()
                df_vacio.name = clave
                dict_from_excel[clave] = df_vacio.convert_dtypes().to_dict()
                hojas_nuevas_info.append({
                    "sheet_name": hoja_nueva,
                    "clave_dict": clave,
                    "header":     0,
                    "usecols":    "A:A",
                    "n_filas":    0,
                    "n_columnas": 0,
                    "columnas":   [],
                })
        _agregar_hojas_a_excel_dict(hojas_nuevas_info)

    else:
        pass
    xls.close()
    xls = None
    return dict_from_excel

# modificado para compatibilidad de json (abr2026)
def dicts_to_dfs(main_dict: dict) -> dict:
    dfs_dict = {}                                          
    for key, ddict in main_dict.items():                   
        dfs_dict[key] = pd.DataFrame(data = ddict)         
        dfs_dict[key].index = dfs_dict[key].index.astype('int')  
        dfs_dict[key] = dfs_dict[key].sort_index()         
    return dfs_dict  

#función que toma el diccionario de dataframes y genera localmente los .dat
def write_dat_files(df_dict: dict, out_path: str, opts_dict: dict, filter_files: list = None) -> None:
    simopt0 = opts_dict["SIM0"]  
    apeopt0 = opts_dict["APE0"]  
    auxopt0 = opts_dict["AUX0"]  
    ULTANO  = opts_dict["UANO"]  
    HIDESP  = opts_dict["HIDE"]  
    NAPEF   = opts_dict["NAPEF"] 
    CDEC    = opts_dict["CDEC"]  
    Aflu4s  = opts_dict["AFL4"]  
    macro_profile = opts_dict.get("macro_profile") 
    
    # mar2026: leer Nº Bloques directamente desde el Excel (hoja Etapas)
    df_etapas_tmp = df_dict['etapas'].dropna(subset=['Etapa', 'Nº Bloques'])  
    blodur = {}           
    nbloques_found = set() 
    for _, row in df_etapas_tmp.iterrows():  
        eta = int(row['Etapa'])              
        nbl = int(row['Nº Bloques'])         
        if nbl not in BLOQUES_CONFIG:        
            raise ValueError(f"Nº Bloques = {nbl} en etapa {eta} no es soportado. Valores válidos: {list(BLOQUES_CONFIG.keys())}.") 
        blodur[eta] = BLOQUES_CONFIG[nbl]    
        nbloques_found.add(nbl)             
    # print(f"Leyendo desde Excel: Se encontraron etapas con {sorted(list(nbloques_found))} bloques.")  
    # print("Procesando bloques y demanda inicial")
    df_dict = process_blodem(df_dict, blodur) 
    df_dict['centrales'].columns = CEN_COLS  
    
    def should_generate(filename):
        if not filter_files:
            return True
        # Soporta tanto nombres exactos como nombres sin extensión
        return filename in filter_files or filename.replace('.dat', '') in filter_files

    etapas_dict = {'etapas': {'NETAPAS': 0, 'DATA': []}}
    if should_generate("plpeta.dat"):
        print("Generando plpeta.dat")
        try:
            etapas_dict = get_etapas_dict(df_dict, macro_profile)  
        except Exception as e:
            pass

    bloque_dict = {'bloques': {'NBLO': 0, 'DATA': []}}
    if should_generate("plpblo.dat"):
        print("Generando plpblo.dat")
        try:
            bloque_dict = get_bloques_dict(df_dict)  
        except Exception as e:
            pass

    barras_dict = {'barras': {'NBARRAS': 0, 'BNAMES': []}}
    if should_generate("plpbar.dat"):
        print("Generando plpbar.dat")
        try: 
            barras_dict = get_barras_dict(df_dict)  
        except Exception as e:
            pass

    lineas_dict = {'lineas': {'NLINEAS': 0, 'MODPRED': 'T', 'PERDERM': 'M', 'REFANG': '1000.d0', 'DATA': []}}
    if should_generate("plpcnfli.dat"):
        print("Generando plpcnfli.dat")
        try:
            lineas_dict = get_lineas_dict(df_dict)  
        except Exception as e:
            pass

    lajam_dict = {}
    if should_generate("plplajam.dat"):
        print("Generando plplajam.dat")
        try:
            lajam_dict = get_lajam_dict(df_dict)  
        except Exception as e:
            pass

    maulen_dict = {}
    if should_generate("plpmaulen.dat"):
        print("Generando plpmaulen.dat")
        try:
            maulen_dict = get_maulen_dict(df_dict)  
        except Exception as e:
            pass

    centrales_dict = {'centrales': {'NCEN': 0, 'NEMB': 0, 'NSER': 0, 'NFALLA': 0, 'NPAS': 0, 'EMBALSES': [], 'SERIES': [], 'TERMICAS': [], 'PASADAS': []}}
    if should_generate("plpcnfce.dat"):
        print("Generando plpcnfce.dat")
        try:
            centrales_dict = get_cnfcen_dict(df_dict, macro_profile=macro_profile)  
        except Exception as e:
            pass

    simape_dict = {'idsim': {'NSIMUL': 0, 'NFIL': 0, 'DATA': []}, 'idape': {'NSIMUL': 0, 'NFIL': 0, 'DATA': {}}, 'idape2': {'NFIL': 0, 'DATA': []}}
    if should_generate("plpidsim.dat") or should_generate("plpidape.dat") or should_generate("plpidap2.dat"):
        print("Generando plpidsim.dat, plpape.dat, plpape2.dat")
        try:
            simape_dict = get_simape_dict(df_dict, simopt0, apeopt0, auxopt0, ULTANO, HIDESP, NAPEF)  
        except Exception as e:
            pass

    aflce_dict = {'aflce': {'NCAU': 0, 'NHIDRO': 0, 'NOMCAU': [], 'NETA': 0, 'MESETA': [], 'QETA': {}}}
    if should_generate("plpaflce.dat"):
        print("Generando plpaflce.dat")
        try:
            aflce_dict = get_aflce_dict(df_dict, simopt0, Aflu4s, macro_profile)  
        except Exception as e:
            pass

    cosce_dict = {'cosce': {'IMANT': 0, 'DATA': [], 'NFIL': 0, 'CVARETA': {}, 'MANTCEN': {}, 'IMES': []}}
    if should_generate("plpcosce.dat"):
        print("Generando plpcosce.dat")
        try:
            cosce_dict = get_cosce_dict(df_dict, macro_profile)  
        except Exception as e:
            pass

    manem_dict = {'mantemb': {'NEMB': 0, 'DATA': {}}}
    if should_generate("plpmanem.dat"):
        print("Generando plpmanem.dat")
        try: 
            manem_dict = get_manem_dict(df_dict)
        except Exception as e:
            pass

    manemh_dict = {'manemh': {}}
    if should_generate("plpminembh.dat"):
        print("Generando plpmanemh.dat")
        try:
            manemh_dict = get_manemh_dict(df_dict)  
        except Exception as e:
            pass

    manli_dict = {'mantlin': {'NMANT': 0, 'LINEAS': [], 'DATA': {}}}
    if should_generate("plpmanli.dat"):
        print("Generando plpmanli.dat")
        try:
            manli_dict = get_manli_dict(df_dict)  
        except Exception as e:
            pass

    dem_dict = {'demanda': {'NDem': 0, 'DATA1': [], 'DATA2': {}, 'DATA3': []}}
    if should_generate("plpdem.dat"):
        print("Generando plpdem.dat")
        try:
            dem_dict = get_demanda_dict(df_dict)  
        except Exception as e: 
            pass

    plem1_dict = {'plem1': {'DATA': []}}
    if should_generate("plpplem1.dat"):
        print("Generando plpplem1.dat")
        try:
            plem1_dict = get_plem1_dict(df_dict)  
        except Exception as e:
            pass

    mant_dict = {'mantcen': {'NTOT': 0, 'DATA': {}, 'CEN': []}, 'mantcen_falla': {'NTOT': 0, 'DATA': {}, 'CEN': []}}
    if should_generate("plpmancen.dat") or should_generate("plpmance.dat"):
        print("Generando plpmancen.dat / plpmance.dat")
        try:
            mant_dict = get_mant_dict2(df_dict, macro_profile=macro_profile)  
        except Exception as e:
            pass

    bat_dict = {'cenbat': {'NBAT': 0, 'MAXINJ': 1, 'DATA': []}}
    if should_generate("plpcenbat.dat"):
        print("Generando plpcenbat.dat")
        try:
            bat_dict = get_cenbat_dict(df_dict)  
        except Exception as e:
            pass

    extr_dict  = {'extracciones': {'NCEN': 0, 'DATA': np.empty((0,3))}}  
    rend_dict  = {'rendimientos': {'NEMB': 0, 'DATA': np.empty((0,8))}}  
    reb_dict   = {'rebalses': {'NEMB': 0, 'DATA': np.empty((0,3))}}  
    filt_dict  = {'filtraciones': {'NEMB': 0, 'fixed': np.empty((0,6)), 'DATA': {}}}  
    cpmax_dict = {'cenpmax': {'NEMB': 0, 'fixed': np.empty((0,3)), 'DATA': {}}}  
    if not CDEC:  
        if should_generate("plpextrac.dat"):
            print("Generando plpextrac.dat")
            try:
                extr_dict = get_extrac_dict(df_dict)  
            except Exception as e:
                pass
        
        if should_generate("plpcenre.dat"):
            print("Generando plpcenre.dat")
            try:
                rend_dict = get_cerend_dict(df_dict)  
            except Exception as e:
                pass
        
        if should_generate("plpvrebemb.dat"):
            print("Generando plpvrebemb.dat")
            try:
                reb_dict = get_rebemb_dict(df_dict)  
            except Exception as e:
                pass
        
        if should_generate("plpfilemb.dat"):
            print("Generando plpfilemb.dat")
            try:
                filt_dict = get_filemb_dict(df_dict)  
            except Exception as e:
                pass
        
        if should_generate("plpcenpmax.dat"):
            print("Generando plpcenpmax.dat")
            try:
                cpmax_dict = get_cepmax_dict(df_dict) 
            except Exception as e:
                pass
        
    # diccionario maestro que asocia cada nombre de archivo .dat con su tupla (diccionario de datos, plantilla de texto)
    all_dict = {
        'plpeta.dat'     : (etapas_dict, ETA_TMPL),     
        'plpbar.dat'     : (barras_dict, BAR_TMPL),     
        'plpblo.dat'     : (bloque_dict, BLO_TMPL),      
        'plpcnfli.dat'   : (lineas_dict, LIN_TMPL),     
        'plplajam.dat'   : (lajam_dict, LAJ_TMPL),     
        'plpmaulen.dat'  : (maulen_dict, MAU_TMPL),     
        'plpcnfce.dat'   : (centrales_dict, CEN_TMPL),  
        'plpidsim.dat'   : (simape_dict, SIM_TMPL),     
        'plpidape.dat'   : (simape_dict, APE_TMPL),     
        'plpidap2.dat'   : (simape_dict, AP2_TMPL),     
        'plpmanem.dat'   : (manem_dict , EMB_TMPL),     
        'plpminembh.dat' : (manemh_dict, EMH_TMPL),    
        'plpmanli.dat'   : (manli_dict , MLI_TMPL),     
        'plpcosce.dat'   : (cosce_dict , COS_TMPL),     
        'plpaflce.dat'   : (aflce_dict , AFL_TMPL),     
        'plpdem.dat'     : (dem_dict , DEM_TMPL),       
        'plpmance.dat'   : (mant_dict, MANT_TMPL),      
        'plpextrac.dat'  : (extr_dict, EXT_TMPL),       
        'plpcenre.dat'   : (rend_dict, REN_TMPL),       
        'plpvrebemb.dat' : (reb_dict, REB_TMPL),        
        'plpfilemb.dat'  : (filt_dict, FIL_TMPL),       
        'plpcenpmax.dat' : (cpmax_dict, PMX_TMPL),      
        'plpplem1.dat'   : (plem1_dict, PLEM1_TMPL),    
        'plpcenbat.dat'  : (bat_dict, BAT_TMPL),        
    }
    
    main_dict = {k: v for k, v in all_dict.items() if should_generate(k)}

    out_path = os.path.normpath(out_path)  
    print("Escribiendo archivos .dat")
    generate_dat_files(out_path, main_dict)  
    print("Escribiendo indhor.csv")
    write_indhor(df_dict['blodem'], os.path.join(out_path, 'indhor.csv'))  
    

 



