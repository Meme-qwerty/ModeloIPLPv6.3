import pandas as pd
import numpy as np
import os
import sys
import warnings

from contenedores_auxiliares import EXCEL_DICT, CEN_COLS, BLOQUES_CONFIG
from templates_dat import *
from dict_creators import *
from utils import *

def parse_from_excel_to_dict(path_to_excel: str)-> dict:
    
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
    
    pexcel = os.path.normpath(path_to_excel)
    
    # check if file exists
    
    if not os.path.isfile(pexcel):
        raise FileNotFoundError(" No se encuentra el archivo {} en la ruta indicada".format(pexcel))
        
    dkeys = list(EXCEL_DICT.keys())
    sheeets = []
    usecols = []
    headers = []
    kkeys = []
    for name, dd in EXCEL_DICT.items():
        sheeets.append(dd['sheet_name'])
        usecols.append(dd['usecols'])
        headers.append(dd['header'])
        kkeys.append(name)
    
    dict_from_excel = {}
    
    xls = pd.ExcelFile(pexcel)
    
    for ws, c, h, k in zip(sheeets, usecols, headers, kkeys):
        try:
            print(f"Leyendo hoja: {ws}")
            df_test = pd.read_excel(xls, sheet_name=ws, usecols=c, header = h)
            df_test.name=k
            dict_from_excel[k]=df_test.convert_dtypes().to_dict()
        except Exception as e:
            df_test = pd.DataFrame()
            df_test.name=k
            dict_from_excel[k]=df_test.convert_dtypes().to_dict()
            continue

    xls.close()
    df_test = None
    xls = None
    
    return dict_from_excel
    
    
# funcion que toma un diccionario de diccionarios y lo transforma a un diccionario de dataframes
# modificado para compatibilidad de json (jul2025)
def dicts_to_dfs(main_dict: dict) -> dict:
    dfs_dict = {}   
    for key, ddict in main_dict.items():
        dfs_dict[key] = pd.DataFrame(data = ddict)
        dfs_dict[key].index = dfs_dict[key].index.astype('int')
        dfs_dict[key] = dfs_dict[key].sort_index() 
    return dfs_dict

# función que toma el diccionario de dataframes y genera localmente los .dat
def write_dat_files(df_dict: dict, out_path: str, opts_dict: dict) -> None:
    
    simopt0 = opts_dict["SIM0"]  ## TipoSimulacion
    apeopt0 = opts_dict["APE0"]  ## TipoAleatorio
    auxopt0 = opts_dict["AUX0"]  ## TipoSimulacion2
    ULTANO  = opts_dict["UANO"]  ## bool
    HIDESP  = opts_dict["HIDE"]  ## bool
    NAPEF   = opts_dict["NAPEF"] ## bool
    CDEC    = opts_dict["CDEC"]  ## bool
    Aflu4s  = opts_dict["AFL4"]  ## bool
    
    # mar2026: leer Nº Bloques directamente desde el Excel (hoja Etapas)
    df_etapas_tmp = df_dict['etapas'].dropna(how='all').dropna(how='any')
    
    blodur = {}
    nbloques_found = set()
    
    for _, row in df_etapas_tmp.iterrows():
        eta = int(row['Etapa'])
        nbl = int(row['Nº Bloques'])
        if nbl not in BLOQUES_CONFIG:
            raise ValueError(f"Nº Bloques = {nbl} en etapa {eta} no es soportado. Valores válidos: {list(BLOQUES_CONFIG.keys())}.")
        blodur[eta] = BLOQUES_CONFIG[nbl]
        nbloques_found.add(nbl)
        
    print(f"Leyendo desde Excel: Se encontraron etapas con {sorted(list(nbloques_found))} bloques.")
    
    print("Procesando bloques y demanda inicial")
    df_dict = process_blodem(df_dict, blodur) # esto agrega dataframes auxiliares

    # machucon horrible para falta de nombres en los headers
    df_dict['centrales'].columns = CEN_COLS
    
    # lo que sigue se puede hacer en un ciclo for, por claridad se hace unfolded
    
    # Los try except crean una advertencia en caso de no encontrar datos para generar el .dat
    #### plpeta.dat
    print("Generando plpeta.dat")
    try:
        etapas_dict = get_etapas_dict(df_dict)
    except Exception as e:
        print(f"Advertencia plpeta.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        etapas_dict = {'etapas': {'NETAPAS': 0, 'DATA': []}}
    
    ### plpblo.dat -> faltaba agregado nov2024
    print("Generando plpblo.dat")
    try:
        bloque_dict = get_bloques_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpblo.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        bloque_dict = {'bloques': {'NBLO': 0, 'DATA': []}}

    #### plpbar.dat
    print("Generando plpbar.dat")
    try: 
        barras_dict = get_barras_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpbar.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        barras_dict = {'barras': {'NBARRAS': 0, 'BNAMES': []}}
    
    ### plpcnfli.dat
    print("Generando plpcnfli.dat")
    try:
        lineas_dict = get_lineas_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpcnfli.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        lineas_dict = {'lineas': {'NLINEAS': 0, 'MODPRED': 'T', 'PERDERM': 'M', 'REFANG': '1000.d0', 'DATA': []}}    
    
    ### plplaja.dat
    print("Generando plplajam.dat")
    try:
        lajam_dict = get_lajam_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plplajam.dat: datos no disponibles ({type(e).__name__}: {e}). El archivo no será generado.")
        lajam_dict = {}
    
    ### plpmaule.dat
    print("Generando plpmaulen.dat")
    try:
        maulen_dict = get_maulen_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpmaulen.dat: datos no disponibles ({type(e).__name__}: {e}). El archivo no será generado.")
        maulen_dict = {}
    
    ### plpcnfce.dat
    print("Generando plpcnfce.dat")
    try:
        centrales_dict = get_cnfcen_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpcnfce.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        centrales_dict = {'centrales': {'NCEN': 0, 'NEMB': 0, 'NSER': 0, 'NFALLA': 0, 'NPAS': 0, 'EMBALSES': [], 'SERIES': [], 'TERMICAS': [], 'PASADAS': []}}

    
    ### plpidsim.dat, plpape.dat, plpape2.dat
    print("Generando plpidsim.dat, plpape.dat, plpape2.dat")
    try:
        simape_dict = get_simape_dict(df_dict, simopt0, apeopt0, auxopt0, ULTANO, HIDESP, NAPEF)
    except Exception as e:
        print(f"  Advertencia plpidsim.dat/plpape.dat/plpape2.dat: datos no disponibles ({type(e).__name__}: {e}). Se generarán con 0 elementos.")
        simape_dict = {'idsim': {'NSIMUL': 0, 'NFIL': 0, 'DATA': []}, 'idape': {'NSIMUL': 0, 'NFIL': 0, 'DATA': {}}, 'idape2': {'NFIL': 0, 'DATA': []}}
    
    ### plpaflce.dat
    print("Generando plpaflce.dat")
    try:
        aflce_dict = get_aflce_dict(df_dict, simopt0, Aflu4s)
    except Exception as e:
        print(f"  Advertencia plpaflce.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        aflce_dict = {'aflce': {'NCAU': 0, 'NHIDRO': 0, 'NOMCAU': [], 'NETA': 0, 'MESETA': [], 'QETA': {}}}

    ### plpcosce.dat
    print("Generando plpcosce.dat")
    try:
        cosce_dict = get_cosce_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpcosce.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        cosce_dict = {'cosce': {'IMANT': 0, 'DATA': [], 'NFIL': 0, 'CVARETA': {}, 'MANTCEN': {}, 'IMES': []}}

    ### plpmanem.dat
    print("Generando plpmanem.dat")
    try: 
        manem_dict = get_manem_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpmanem.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        manem_dict = {'mantemb': {'NEMB': 0, 'DATA': {}}}
    
    ### plpmanemh.dat
    print("Generando plpmanemh.dat")
    try:
        manemh_dict = get_manemh_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpminembh.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        manemh_dict = {'manemh': {}}
    
    ### plpmanli.dat
    print("Generando plpmanli.dat")
    try:
        manli_dict = get_manli_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpmanli.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        manli_dict = {'mantlin': {'NMANT': 0, 'LINEAS': [], 'DATA': {}}}
    
    ### plpdem.dat
    print("Generando plpdem.dat")
    try:
        dem_dict = get_demanda_dict(df_dict)
    except Exception as e: 
        print(f"  Advertencia plpdem.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        dem_dict = {'demanda': {'NDem': 0, 'DATA1': [], 'DATA2': {}, 'DATA3': []}}
    
    ### plpplem1.dat
    print("Generando plpplem1.dat")
    try:
        plem1_dict = get_plem1_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpplem1.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        plem1_dict = {'plem1': {'DATA': []}}

    ### plpmancen.dat
    print("Generando plpmancen.dat")
    try:
        mant_dict = get_mant_dict2(df_dict)
    except Exception as e:
        print(f"  Advertencia plpmancen.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        mant_dict = {'mantcen': {'NTOT': 0, 'DATA': {}, 'CEN': []}, 'mantcen_falla': {'NTOT': 0, 'DATA': {}, 'CEN': []}}
    
    
    
    
    extr_dict  = {}
    rend_dict  = {}
    reb_dict   = {}
    filt_dict  = {}
    cpmax_dict = {}
    bat_dict   = {}

    ### plpcenbat.dat
    print("Generando plpcenbat.dat")
    try:
        bat_dict = get_cenbat_dict(df_dict)
    except Exception as e:
        print(f"  Advertencia plpcenbat.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
        bat_dict = {'cenbat': {'NBAT': 0, 'MAXINJ': 1, 'DATA': []}}

    if not CDEC:
        ### plpextrac.dat
        print("Generando plpextrac.dat")
        try:
            extr_dict = get_extrac_dict(df_dict)
        except Exception as e:
            print(f"  Advertencia plpextrac.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
            extr_dict = {'extracciones': {'NCEN': 0, 'DATA': np.empty((0,3))}}
        
        ### plpcenre.dat
        print("Generando plpcenre.dat")
        try:
            rend_dict = get_cerend_dict(df_dict)
        except Exception as e:
            print(f"  Advertencia plpcenre.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
            rend_dict = {'rendimientos': {'NEMB': 0, 'DATA': np.empty((0,8))}}
        
        ### plpvrebemb.dat
        print("Generando plpvrebemb.dat")
        try:
            reb_dict = get_rebemb_dict(df_dict)
        except Exception as e:
            print(f"  Advertencia plpvrebemb.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
            reb_dict = {'rebalses': {'NEMB': 0, 'DATA': np.empty((0,3))}}
        
        ### plpfilemb.dat
        print("Generando plpfilemb.dat")
        try:
            filt_dict = get_filemb_dict(df_dict)
        except Exception as e:
            print(f"  Advertencia plpfilemb.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
            filt_dict = {'filtraciones': {'NEMB': 0, 'fixed': np.empty((0,6)), 'DATA': {}}}
        
        ### plpcenpmax.dat
        print("Generando plpcenpmax.dat")
        try:
            cpmax_dict = get_cepmax_dict(df_dict)
        except Exception as e:
            print(f"  Advertencia plpcenpmax.dat: datos no disponibles ({type(e).__name__}: {e}). Se generará con 0 elementos.")
            cpmax_dict = {'cenpmax': {'NEMB': 0, 'fixed': np.empty((0,3)), 'DATA': {}}}
        
    # editado may2025
    main_dict = {
        'plpeta.dat'     : (etapas_dict, ETA_TMPL),
        'plpbar.dat'     : (barras_dict, BAR_TMPL),
        'plpblo.dat'     : (bloque_dict, BLO_TMPL), # agregado, faltaba a nov2024
        'plpcnfli.dat'   : (lineas_dict, LIN_TMPL),
        'plplajam.dat'   : (lajam_dict, LAJ_TMPL),
        'plpmaulen.dat'  : (maulen_dict, MAU_TMPL),
        'plpcnfce.dat'   : (centrales_dict, CEN_TMPL),
        'plpidsim.dat'   :  (simape_dict, SIM_TMPL),
        'plpidape.dat'   :  (simape_dict, APE_TMPL),
        'plpidap2.dat'   :  (simape_dict, AP2_TMPL),
        'plpmanem.dat'   :  (manem_dict , EMB_TMPL),
        'plpminembh.dat' :  (manemh_dict, EMH_TMPL),
        'plpmanli.dat'   :  (manli_dict , MLI_TMPL),
        'plpcosce.dat'   :  (cosce_dict , COS_TMPL),
        'plpaflce.dat'   :  (aflce_dict , AFL_TMPL),
        'plpdem.dat'     :  (dem_dict , DEM_TMPL),
        'plpmancen.dat'  :  (mant_dict, MANT_TMPL),
        'plpextrac.dat'  :  (extr_dict, EXT_TMPL),
        'plpcenre.dat'   :  (rend_dict, REN_TMPL),
        'plpvrebemb.dat' :  (reb_dict, REB_TMPL),
        'plpfilemb.dat'  :  (filt_dict, FIL_TMPL),
        'plpcenpmax.dat' :  (cpmax_dict, PMX_TMPL),
        'plpplem1.dat'   :  (plem1_dict, PLEM1_TMPL),
        'plpcenbat.dat'  :  (bat_dict, BAT_TMPL),       # agregado mar2026
           
    }
    
    out_path = os.path.normpath(out_path)
    
    print("Escribiendo archivos .dat")
    generate_dat_files(out_path, main_dict)
    
    #### ancillary file
    print("Escribiendo indhor.csv")
    write_indhor(df_dict['blodem'], os.path.join(out_path, 'indhor.csv'))
    
### funciones TEMPORALES adicionales para facilitar revisión oct2024
def test_mancen(path_to_excel: str, out_path: str, write_dat = True) -> dict:
    '''
    Función que solo ejecuta el mínimo de subrutinas de modo de correr la rutina de generación de mantenimientos.
    
    Params:
        path_to_excel: Ruta completa (absoluta o relativa) el archivo xlsm (CEN).
        out_path: Ruta de salida para archivo .dat. Solo ruta, sin nombre de archivo.
    '''
    
    
    import os
    import time
    from templates_dat import MANT_TMPL
    
    
    excel_dict = parse_from_excel_to_dict(os.path.normpath(path_to_excel))
    dict_df = dicts_to_dfs(excel_dict)
    df_dict = process_blodem(dict_df)
    
    t0 = time.perf_counter()
    mant_dict = get_mant_dict(df_dict)
    t1 = time.perf_counter()
    
    if write_dat:
        write_to = os.path.join(os.path.normpath(out_path), os.path.normpath('./plpmancen.dat'))
        print(write_to)
        generate_file(MANT_TMPL, mant_dict,  write_to)
    
    print("Total elapsed time for MANT routine: ", t1-t0)
    return mant_dict

def read_mancen_from_dat(path_to_dat: str) -> dict:
    '''
    Función auxiliar que toma un archivo plpmance.dat y lo transforma en un diccionario de dataframes.
    
    Params:
        path_to_dat: Ruta absoluta o relativa al archivo. Debe incluir el nombre de este.
        
    Returns:
        Diccionario cuyas llaves son los nombres de las centrales y cuyos valores son pd.DataFrames.
    '''
    import os
    
    out_dict = dict()
    with open(os.path.normpath(path_to_dat), 'r') as f:
        _  = f.readline()
        _ = f.readline()
        ncen = int(f.readline().strip().rstrip())

        for icen in range(ncen):
            cen_data = []
            _ = f.readline()
            cnom = f.readline().strip().rstrip().replace("'", "")
            _ = f.readline()
            nblo = int(f.readline().strip().rstrip().split()[0])
            _ = f.readline()
            for iblo in range(nblo):
                mes, blo, _, pmin, pmax = f.readline().strip().rstrip().split()
                blo_data = cen_data.append([int(mes), int(blo), float(pmin), float(pmax)])   
            out_dict[cnom] = pd.DataFrame(columns = ["mes", "bloque", "potmin", "potmax"], data = cen_data)
            
    return out_dict

# validacion de mantenimientos ene2025
def validate_mancen(data_dict : dict) -> tuple:
    dict_df = dicts_to_dfs(data_dict)
    
    df_barr_xls = dict_df['barras'].dropna(subset = "BARRA").astype({"Nº": 'int32'})
    df_etap_xls = dict_df["etapas"].dropna(subset = "Etapa").astype({"Etapa": "int32"})
    df_cent_xls = dict_df["centrales"]

    df_cini_xls = dict_df["CIniciales"].dropna(subset = "CENTRAL")
    df_pobr_xls = dict_df["PObra"].dropna(subset = "CENTRAL")
    df_limi_xls = dict_df["Limitaciones"].dropna(subset = "CENTRAL")
    df_dcom_xls = dict_df["DispComb"].dropna(subset = "CENTRAL").dropna(how = 'any')
    df_mmay_xls = dict_df["MMayor"].dropna(how = 'any')
    df_ernc_xls = dict_df["ERNC"].drop("Unnamed: 0", axis = 1)

    df_mmay_xls.columns = df_cini_xls.columns
    
    ccount                   = len(df_cent_xls)
    begin_date               = df_etap_xls.loc[0,"Inicial"]
    df_array_cen             = df_cent_xls.iloc[:,[1,2,26,27]].rename(columns = {'Unnamed: 1': 'central', 'Tipo de Central': 'no_riego', 'Mínima.1': 'pminnom','Máxima.1': 'pmaxnom'})
    df_array_cen['mant?']    = False
    df_array_cen['aux2']     = 0
    df_array_cen['no_riego'] = df_array_cen['no_riego'] != 'X'
    df_array_cen             = df_array_cen.set_index('central', drop = True)
    df_potnom                = df_cent_xls.iloc[:,[1,27]].copy()
    df_potnom.columns        = ['CENTRAL', 'potmaxnom']
    
    centrales = list(df_array_cen.index.unique())
    
    cini_centrales = df_cini_xls.CENTRAL.unique().tolist()
    pobr_centrales = df_pobr_xls.CENTRAL.unique().tolist()
    mmay_centrales = df_mmay_xls.CENTRAL.unique().tolist()
    dcom_centrales = df_dcom_xls.CENTRAL.unique().tolist()
    limi_centrales = df_limi_xls.CENTRAL.unique().tolist()
    ernc_centrales = df_ernc_xls.CENTRAL.unique().tolist()
    
    mants  = [cini_centrales, pobr_centrales, mmay_centrales, dcom_centrales, limi_centrales, ernc_centrales]
    dfs    = [df_cini_xls, df_pobr_xls, df_mmay_xls, df_dcom_xls, df_limi_xls, df_ernc_xls]
    nmants = [len(df) for df in dfs]
    status = []

    # chequeo de existencia de centrales con mantenimiento en lista de centrales original
    fail = []
    good = []
    rows = []
    for k, mlist in enumerate(mants):
        dfmant    = dfs[k]
        fail_list = chequea_centrales(centrales, mlist)
        nfail     = 0

        if fail_list:
            good_pplant = [cen for cen in mlist if cen not in fail_list]
            nfail       = len(fail_list)
            status.append("ERROR")
        else:
            good_pplant = mlist
            status.append("OK")

        good.append(good_pplant)

        df_array_cen.loc[good_pplant, "mant?"] = True
        fail.append(fail_list)
    
    hojas = ["C.Iniciales(1)", "Plan de Obras (5)", "Mantenimiento Mayor(4)", "Disp. Combustibles", "Limitaciones(3)", "ERNC(6)", "Plan de Obras/ERNC"]
    
    error_data = []
    for k, flist in enumerate(fail):
        if flist:
            for c in flist:
                error_data.append([hojas[k], c, "", "Central no encontrada"])
    
    
    
    # chequeo de duplicados en hoja plan de obra
    dups = df_pobr_xls[df_pobr_xls.duplicated(subset = "CENTRAL")]
    
    if dups.empty:
        fail.append([])
        nfail = 0
        status.append("OK")
    else:
        dupli = dups.CENTRAL.unique().tolist()
        nfail = len(dupli)
        fail.append(dupli)
        status.append("ERROR")
        for row in dups.iterrows():
            error_data.append([hojas[-1], row[1].iloc[0], row[0], "Central duplicada PObra"])
        
        
    # generacion de datos de resumen en tabla
    # en este punto 'good' tiene las listas de centrales verificadas y 'fails' los nombres de las centrales con problemas
    # 'nmants' una lista con los números de mantenimientos por conjunto (6)
    df_summary = pd.DataFrame(columns = ["Hoja Proceso","Validacion Central", "Número de Mantenciones", "Consistentes en Fechas M", "No Procesar por Fecha", "Potencia Inconsitente M", "Potencia Inconsistente C"])

    

    for k, nm in enumerate(nmants):
        hoj = hojas[k]
        st  = status[k]
        row = [hoj, st, nm, "", "", "", ""]
        df_summary = pd.concat([df_summary, pd.DataFrame([row], columns = df_summary.columns)], ignore_index = True)

    df_summary = pd.concat([df_summary, pd.DataFrame([["Plan de Obras/ERNC", status[-1], df_summary.iloc[1,2], "", "", "", ""]], columns = df_summary.columns)], ignore_index = True).set_index('Hoja Proceso', drop = True)
        
    # generacion de dataframe de errores
    df_error = pd.DataFrame(columns = ["Hoja", "Central", "Número de fila", "Tipo de error"])
    
    # conteo de fechas, aca no hay errores que reportar solo se filtra
    nprocs = []
    filt_dfs = []
    for k in range(len(dfs) - 1):
        df_mant = dfs[k]
        non_proc, df_filt = conteo_de_fechas(df_mant, begin_date)
        nprocs.append(non_proc)
        if non_proc > 0:
            filt_dfs.append(df_filt)
        else:
            filt_dfs.append(df_mant)
    
    filt_dfs.append(df_ernc_xls)
    # ernc
    nprocs.append(0)
    # pobra/ernc
    nprocs.append("")
    df_summary.iloc[:,3] = nprocs
    
    #error_data = []
    ndates_error = []
    npoten_error = []
    npnomi_error = []
    for k, df_mant in enumerate(filt_dfs):
        dfmant_filt = df_mant.copy()
        
        if k < 5:
            error_fecha, dfmant_filt = chequeo_fechas(dfmant_filt)

            if not error_fecha.empty:
                rows = error_fecha.index.tolist()
                cent = error_fecha.CENTRAL.tolist()
                ndates_error.append(len(rows))
                for e in range(len(rows)):
                    error_data.append([hojas[k], cent[e], rows[e], "Fechas inconsistentes"]) 
            else:
                ndates_error.append(0)
        else:
            ndates_error.append(0)
        
        error_consi, dfmant_filt = chequeo_consistencia_potencias(dfmant_filt)
        
        if not error_consi.empty:
            rows = error_consi.index.tolist()
            cent = error_consi.CENTRAL.tolist()
            npoten_error.append(len(rows))
            for e in range(len(rows)):
                error_data.append([hojas[k], cent[e], rows[e], "Potencia inconsitente"])
        else:
            npoten_error.append(0)
                
        error_nomin, dfmant_filt = chequeo_potencia_nominal(dfmant_filt, df_potnom )
        
        if not error_nomin.empty:
            rows = error_nomin.index.tolist()
            cent = error_nomin.CENTRAL.tolist()
            npnomi_error.append(len(rows))
            for e in range(len(rows)):
                error_data.append([hojas[k], cent[e], rows[e], "Potencia inconsistente con potencia máxima nominal"]) 
        else:
            npnomi_error.append(0)
    
    ndates_error.append("")
    npoten_error.append("")
    npnomi_error.append("")
    
    df_summary.iloc[:,2] = ndates_error
    df_summary.iloc[:,4] = npoten_error
    df_summary.iloc[:,5] = npnomi_error
    
    error = False
    if error_data:
        # generacion de dataframe de errores
        df_error = pd.DataFrame(columns = ["Hoja", "Central", "Número de fila", "Tipo de error"], data = error_data)
        error    = True
    else:
        df_error = pd.DataFrame(columns = ["Hoja", "Central", "Número de fila", "Tipo de error"])
        
    return error, df_summary, df_error
