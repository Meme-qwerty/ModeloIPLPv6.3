import pandas as pd
import math
from decimal import Decimal, ROUND_HALF_UP
from contenedores_auxiliares import TAGS_LAJA, TAGS_MAULE
from data_parsers import *
from utils import *

#ETAPAS
def get_etapas_dict(dict_df: dict, macro_profile=None) -> dict:
    df_etapas_xls = dict_df['etapas']
    df_etapas = parse_etapas(df_etapas_xls)
    dict_eta = {'etapas': {
                       'NETAPAS': len(df_etapas),
                       'DATA'  : df_etapas.values
                      }}
    return dict_eta

#BLOQUES
def get_bloques_dict(dict_df: dict) -> dict:
    df_blodem_xls = dict_df['blodem']
    df_blo = parse_bloques(df_blodem_xls)
    MES_MESC = {4:1,5:2,6:3,7:4,8:5,9:6,10:7,11:8, 12:9, 1:10, 2:11, 3:12}
    dict_blo = {'bloques':{'NBLO': int(df_blo["indice"].max()),
                      'DATA': df_blo.values}}
    return dict_blo

#BARRAS
def get_barras_dict(dict_df: dict) -> dict:
    df_barras_xls = dict_df['barras']
    df_barras = parse_barras(df_barras_xls)
    dict_bar = {'barras': {'NBARRAS': len(df_barras), 'BNAMES': df_barras["BARRA"].values.tolist()}}
    return dict_bar

#LINEAS
#editado abril026
def get_lineas_dict(dict_df: dict, modpred: str = 'T', perderm: str = 'M', refang :str = "1000.d0") -> dict:
    df_lineas_xls = dict_df['lineas']
    df_lineas = parse_lineas(df_lineas_xls)
    df_lineas = correccion_preredondeo(df_lineas, ['R[ohm]', 'X[ohm]'], 3)
    df_lineas = correccion_preredondeo(df_lineas, ['A->B', 'B->A'], 1)
    dict_lin = {'lineas': {'NLINEAS': len(df_lineas), 
                       'MODPRED': modpred, 
                       'PERDERM': perderm, 
                       'REFANG': refang, 
                       'DATA'  : df_lineas.values
                      }}
    return dict_lin

#EXTRACCIONES
def get_extrac_dict(dict_df: dict) -> dict:
    df_extracciones_xls = dict_df['Extracciones']
    df_extr = parse_extracciones(df_extracciones_xls)
    dict_extr = { 'extracciones': {
                 'NCEN': len(df_extr),
                 'DATA': df_extr.values}
    }
    return dict_extr

#RENDIMIENTOS
def get_cerend_dict(dict_df: dict) -> dict:
    df_rendimientos_xls = dict_df['Rendimientos']
    df_centrales_xls    = dict_df['centrales']
    df_rend = parse_rendimientos(df_rendimientos_xls, df_centrales_xls)
    dict_rend = {'rendimientos': {
                'NEMB': len(df_rend['central'].unique().tolist()),
                'DATA': df_rend.values}
    }
    return dict_rend

#FILTRACIONES
def get_filemb_dict(dict_df: dict) -> dict:    
    df_filtraciones_xls = dict_df['Filtraciones']
    df_centrales_xls    = dict_df['centrales']
    df_aux, df_aux2, embnames = parse_filtraciones(df_filtraciones_xls, df_centrales_xls)
    dict_filt = { 'filtraciones': {
                 'NEMB' : len(df_filtraciones_xls['central'].unique().tolist()),
                 'fixed': df_aux.values,
                 'DATA' :{name: df_aux2.loc[name, :].values for name in embnames}}             
    }
    return dict_filt

#REBALSES
def get_rebemb_dict(dict_df: dict) -> dict:    
    df_rebalses_xls = dict_df['Rebalse']
    df_reb = parse_rebalses(df_rebalses_xls)
    dict_reb = {'rebalses':{'NEMB': len(df_reb), 
                       'DATA'  : df_reb.values}}
    return dict_reb

#BATERIAS
def get_cenbat_dict(dict_df: dict) -> dict:
    df_bat_xls = dict_df['Baterias']
    df_bat = parse_baterias(df_bat_xls)
    data = []
    for _, row in df_bat.iterrows():
        indice = int(row['INDICE'])
        baterias = str(row['BATERIAS']).strip()
        barra = int(row['Conectada a la Barra'])
        # Corrección: BAT_MARIA_ELENA_FV (índice 29) barra debe ser 76, no 75
        if indice == 29 and barra == 75:
            barra = 76
        rendimiento_desc = float(row['Rendimiento de Descarga'])
        cap_min = float(row['Mínima'])
        cap_max = float(row['Máxima'])
        cen_carga = str(row['Central de Carga'])
        rendimiento_carga = float(row['Rendimiento de Carga'])
        data.append((indice, baterias, barra, rendimiento_desc, cap_min, cap_max, cen_carga, rendimiento_carga))
    return {'cenbat': {'NBAT': len(data), 'MAXINJ': 1, 'DATA': data}}

#CENPMAX
def get_cepmax_dict(dict_df: dict) -> dict:   
    df_cenpmax_xls = dict_df['CenPmax']
    df_aux, df_aux2, embnames = parse_cenpmax(df_cenpmax_xls)
    dict_cpmax = { 'cenpmax': {
                 'NEMB' : len(embnames),
                 'fixed': df_aux.values,
                 'DATA' :{name: df_aux2.loc[name, :].values for name in embnames}}             
    }
    return dict_cpmax

#LAJA 
#mar2026 
def get_lajam_dict(dict_df: dict, tags: dict = TAGS_LAJA) -> dict:
    df_laja_xls = dict_df['LAJAM']
    out = {'laja': {}}
    for index, row in df_laja_xls.iterrows():
        if index >= len(tags): continue
        name, typ, coerce = tags[index]
        if not name or not coerce: continue
        
        # Función auxiliar para aplicar coerce de forma segura
        def safe_coerce(val, func):
            if pd.isna(val) or str(val).strip().lower() == 'nan' or str(val).strip() == '':
                return None
            try:
                if func == int:
                    # Usar float() primero para manejar strings como "4.0"
                    return int(float(val))
                return func(val)
            except (ValueError, TypeError):
                return None

        # --- Extracción de DATOS ---
        if typ:
            # Para LISTAS: n siempre está en la Columna C (índice 2)
            # Los datos empiezan en la Columna D (índice 3)
            n_raw = safe_coerce(row.iloc[2], int)
            n_val = n_raw if n_raw is not None else 0
            value = []
            if n_val > 0:
                for i in range(n_val):
                    c_idx = 3 + i # Empezar en D
                    if c_idx < len(row):
                        v = safe_coerce(row.iloc[c_idx], coerce)
                        default_val = 0 if coerce == int else (0.0 if coerce == float else "")
                        value.append(v if v is not None else default_val)
            out['laja'][name] = value
        else:
            # Para ESCALARES: por defecto la D (índice 3), con la excepción histórica de NumEtaQForz que va en la C (índice 2)
            if name == 'NumEtaQForz':
                value = safe_coerce(row.iloc[2], coerce)
            else:
                value = safe_coerce(row.iloc[3], coerce)
            # Si no se encontró nada, asignar valor por defecto
            if value is None:
                value = 0 if coerce == int else (0.0 if coerce == float else "")
            out['laja'][name] = value
    return out

#MAULE
def get_maulen_dict(dict_df: dict, tags: dict = TAGS_MAULE) -> dict:
    df_maule_xls = dict_df['MAULEN']
    out = {'maule': {}}
    for index, row in df_maule_xls.iterrows():
        #print(index, row)
        if index > 51: continue
        name, typ, coerce = tags[index]
        if not name: continue
        n = int(row.iloc[2])
        if not isinstance(coerce, list):
            if typ:
                value = list(map(coerce, row.iloc[3:(3+n)].to_list()))
                value = [x for x in value if str(x) != 'nan']
            else:
                value = coerce(row.iloc[3])
        else:
            if typ:
                value = []
                for i in range(n):
                    value.append(row.iloc[(3+i)])
        out['maule'][name] = value
    out['maule']['PorRet'] = [str(por) for por in out['maule']['PorRet']]
    return out
#CENTRALES
# mar2026
def get_cnfcen_dict(dict_df: dict, uninodal: bool = False, macro_profile=None) -> dict:
    df_centrales_xls = dict_df['centrales']
    embalses, series, pasadas, termicas, fallas, baterias, ncen = parse_centrales(df_centrales_xls, uninodal)
    embalses['FEsc'] = embalses.FEsc.astype(str).apply(lambda x: "1.0E+{}".format(x.count('0')))
    termicas[['vertmin', 'vertmax']] = termicas[['vertmin', 'vertmax']].replace(np.nan, 0.0)
    baterias[['vertmin', 'vertmax']] = baterias[['vertmin', 'vertmax']].replace(np.nan, 0.0)
    fallas[['vertmin', 'vertmax']]   = fallas[['vertmin', 'vertmax']].replace(np.nan, 0.0)
    
    # Columnas con 1 decimal (potencias, costos, afluentes)
    cols_1 = ['potmax', 'potmin', 'vertmin', 'vertmax', 'cvariable', 'afl1ersem']
    termicas  = correccion_preredondeo(termicas, cols_1, 1)
    series    = correccion_preredondeo(series, cols_1, 1)
    pasadas   = correccion_preredondeo(pasadas, cols_1, 1)
    fallas    = correccion_preredondeo(fallas, cols_1, 1)
    embalses  = correccion_preredondeo(embalses, cols_1, 1)
    baterias  = correccion_preredondeo(baterias, cols_1, 1)
    
    # Rendimiento: 3 decimales
    termicas  = correccion_preredondeo(termicas, ['rendimiento'], 3)
    series    = correccion_preredondeo(series, ['rendimiento'], 3)
    pasadas   = correccion_preredondeo(pasadas, ['rendimiento'], 3)
    fallas    = correccion_preredondeo(fallas, ['rendimiento'], 3)
    embalses  = correccion_preredondeo(embalses, ['rendimiento'], 3)
    baterias  = correccion_preredondeo(baterias, ['rendimiento'], 3)
    
    # Volúmenes (solo embalses): 7 decimales
    # embalses  = correccion_preredondeo(embalses, ['volini', 'volfin', 'volmin', 'volmax'], 7, rounding_mode='ROUND_HALF_EVEN')
    has_baterias = False
    if 'Baterias' in dict_df:
        df_bat = dict_df['Baterias']
        if not df_bat.empty or len(df_bat.columns) > 0:
            has_baterias = True
    dict_cen = {'centrales':{'NCEN': ncen, 
                         'NEMB': len(embalses),
                         'NSER': len(series),
                         'NFALLA': len(fallas),
                         'NPAS': len(pasadas),
                         'NBAT': len(baterias),
                         'HAS_BAT_SHEET': has_baterias,
                         'extra_tags': macro_profile.has_extra_tags if macro_profile else False,
                         'EMBALSES': embalses.values,
                         'SERIES': series.values,
                         'TERMICAS': termicas.values,
                         'PASADAS': pasadas.values,
                         'BATERIAS': baterias.values,
                         'FALLAS': fallas.values}}
    return dict_cen

#PLEM1
def get_plem1_dict(dict_df: dict) -> dict:
    """
    Genera el diccionario para plpplem1.dat (embalses con cotas de volumen).
    Volúmenes: Excel en hm3 -> .dat en dam3 (hm3 × 1000).
    FEscala   : int(log10(volmax_m3) + 0.5), donde volmax_m3 = volmax_hm3 × 1e6.
    VolMinNECF/VolMaxNECF: columna 'Volumen Mínimo/Máximo 2S hm3' si está disponible,
                           sino fallback a volmin/volmax.
    """
    df_cen = dict_df['centrales'].copy()
    df_cen = df_cen.rename(columns={
        'INDICE'                 : 'numcen',
        'CENTRALES'              : 'central',
        'Tipo de Central'        : 'tipo',
        'Rendimiento [MWh/m3s]'  : 'rendimiento',
        'Conectada a la Barra'   : 'barra',
        'Mínimo'                 : 'volmin',
        'Máximo'                 : 'volmax',
        'Volumen Mínimo 2S hm3'  : 'volminnecf_xl',
        'Volumen Máximo 2S hm3'  : 'volmaxnecf_xl',
    })
    df_cen = df_cen[~df_cen['numcen'].isna()].reset_index(drop=True)
    df_cen['barra']      = df_cen['barra'].fillna(0).astype('int32')
    df_cen['volmin']     = pd.to_numeric(df_cen['volmin'],     errors='coerce').fillna(0.0)
    df_cen['volmax']     = pd.to_numeric(df_cen['volmax'],     errors='coerce').fillna(0.0)
    df_cen['rendimiento']= pd.to_numeric(df_cen['rendimiento'],errors='coerce').fillna(0.0)
    # solo embalses con almacenamiento
    df_emb = df_cen[df_cen['tipo'].isin(['E', 'A'])].copy()
    # NECF: usar columna 2S si existe y tiene valor; si no, usar volmin/volmax
    for necf_col, base_col in [('volminnecf_xl', 'volmin'), ('volmaxnecf_xl', 'volmax')]:
        if necf_col in df_emb.columns:
            df_emb[necf_col] = pd.to_numeric(df_emb[necf_col], errors='coerce')
            df_emb[necf_col] = df_emb[necf_col].fillna(df_emb[base_col])
        else:
            df_emb[necf_col] = df_emb[base_col]
    # FEscala = exponent of nearest power of 10 to volmax in m3
    def _fescala(volmax_hm3):
        volmax_m3 = max(float(volmax_hm3) * 1e6, 1.0)
        return int(np.log10(volmax_m3) + 0.5)
    data = []
    for _, row in df_emb.iterrows():
        numero     = "{:>3d}".format(int(row['numcen']))
        nombre     = "{:<24s}".format(str(row['central']).strip())
        tipo       = str(row['tipo'])
        barra      = "{:>3d}".format(int(row['barra']))
        na         = "  0"
        volmin     = "{:10.2f}".format(float(row['volmin'])     * 1000.0)
        volmax     = "{:10.2f}".format(float(row['volmax'])     * 1000.0)
        volminnecf = "{:10.2f}".format(float(row['volminnecf_xl']) * 1000.0)
        volmaxnecf = "{:10.2f}".format(float(row['volmaxnecf_xl']) * 1000.0)
        fescala    = "{:3d}".format(_fescala(row['volmax']))
        factrendim = "{:8.3f},".format(float(row['rendimiento']))
        data.append((numero, nombre, tipo, barra, na,
                     volmin, volmax, volminnecf, volmaxnecf, fescala, factrendim))
    return {'plem1': {'DATA': data}}

#AFLUENTES
def get_aflce_dict( dict_df : dict,
                    sim_type  : TipoSimulacion,
                    afl4s: bool  = True,
                    macro_profile = None) -> dict:
    df_hid_xls = dict_df['Hidrologia']   # hoja hidrologia
    df_ah1_xls = dict_df['CaudalesAh1']  # hoja caudales ah1
    df_ah2_xls = dict_df['CaudalesAh2']  # hoja caudales ah2
    df_his_xls = dict_df['Historicos']   # hoja historicos
    df_eta_xls = dict_df['etapas']       # hoja etapas
    df_cen_xls = dict_df['centrales']    # hoja centrales
    df_fla_xls = dict_df['flags']        # hoja datos flags especificos

    if afl4s:
        NCau, NHidro, NombreCau, NEta, MesEta, dict_qeta_lines = parse_afluentes(df_hid_xls, 
                                                                                 df_ah1_xls, 
                                                                                 df_ah2_xls,
                                                                                 df_his_xls,
                                                                                 df_eta_xls,
                                                                                 df_cen_xls,
                                                                                 df_fla_xls,
                                                                                 sim_type)
    else:
        NCau, NHidro, NombreCau, NEta, MesEta, dict_qeta_lines = parse_afluentes_sin_aflu4s(df_hid_xls, 
                                                                                 df_ah1_xls, 
                                                                                 df_ah2_xls,
                                                                                 df_his_xls,
                                                                                 df_eta_xls,
                                                                                 df_cen_xls,
                                                                                 df_fla_xls,
                                                                                 sim_type)
    dict_aflce = {'aflce': {'NCAU': NCau, 'NHIDRO': NHidro, "NOMCAU": NombreCau, "NETA": NEta, "MESETA": MesEta, "QETA": dict_qeta_lines }}
    return dict_aflce
    
    
#COSTOS
def get_cosce_dict( dict_df: dict, macro_profile=None) -> dict:
    df_cos_xls = dict_df['cvariable'] # hoja costos
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    NFil, dict_CVarEta, CenNomFinal, NEtaCen, dict_MantCen, IMant, imes_aux, etapa_list = parse_costos(df_cos_xls, df_eta_xls, df_cen_xls, macro_profile=macro_profile)
    dict_cosce = {'cosce': {"NFIL": NFil, "ETAPAS": etapa_list, "CVARETA": dict_CVarEta, "DATA": zip(CenNomFinal, NEtaCen), "MANTCEN": dict_MantCen, "IMANT": IMant, "IMES": imes_aux}}
    return dict_cosce

#MANTENIMIENTOS EMBALSES
def get_manem_dict( dict_df: dict) -> dict :
    df_emb_xls = dict_df['MantEMB']   # hoja costos
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    my_dict, NEmb = parse_embalses(df_emb_xls, df_eta_xls, df_cen_xls)
    dict_mantemb = {'mantemb': {'DATA': my_dict, 'NEMB': NEmb}}
    return dict_mantemb

#MANTENIMIENTOS EMBALSES H
def get_manemh_dict(dict_df: dict) -> dict :
    df_emh_xls = dict_df['MantEMBh']  # hoja costos
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    NMantEmbMant, MantCen, df_eta, VMinEta, CostoEta = parse_embalsesh(df_emh_xls, df_eta_xls, df_cen_xls)
    manemh_out = {}
    for ename, value in NMantEmbMant.items():
        mask = MantCen[ename]
        if value == 0 or not mask.any():
            data = np.empty((0, 3))
        else:
            data = np.column_stack((
                df_eta.loc[mask, "Etapa"].values,
                VMinEta.loc[mask, ename].values,
                CostoEta.loc[mask, ename].values
            ))
        manemh_out[ename] = {'NMANT': int(value), 'DATA': data}
    dict_manemh = {'manemh': manemh_out}
    return dict_manemh

#MANTENIMIENTOS LINEAS
# modificado abr2026
def get_manli_dict( dict_df: dict) -> dict :
    df_lin_xls = dict_df['lineas']    # hoja lineas
    df_mli_xls = dict_df['manLin']    # hoja mantli
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    df_ml2_xls = dict_df['manLin2']   # datos adicionales
    data_dict, mant_unique, mant_nblo, nmant = parse_mlineas(df_lin_xls, df_mli_xls, df_eta_xls, df_cen_xls, df_ml2_xls)
    dict_mantlin =  {'mantlin': {"DATA": data_dict, "LINEAS": zip(mant_unique, mant_nblo), "NMANT": nmant}}
    return dict_mantlin

#SIMULACIONES Y APERTURAS
def get_simape_dict(dict_df   : dict,    
                    sim_type  : TipoSimulacion,  
                    ale_type  : TipoAleatorio,   
                    si2_type  : TipoSimulacion2, 
                    ULTIMOS_ANOS: bool = True,
                    HIDRO_ESP : bool = False,
                    NO_APERT_FICT: bool = False) -> dict :
    df_hid_xls = dict_df['Hidrologia'] # hoja hidrologia
    df_eta_xls = dict_df['etapas']  # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    NFil, NSimul, txt_data_idsim, data_ape, txt_data_ap2 = parse_simape(df_hid_xls, df_eta_xls, df_cen_xls, sim_type, ale_type, si2_type, ULTIMOS_ANOS, HIDRO_ESP, NO_APERT_FICT)
    dict_simape = {}
    dict_simape['idsim']  = {'NFIL': NFil, 'NSIMUL': NSimul, 'DATA': txt_data_idsim}
    dict_simape['idape']  = {"NSIMUL": NSimul, "NFIL": NFil, "DATA": data_ape}
    dict_simape['idape2'] = {"NFIL": NFil, "DATA": txt_data_ap2}
    return dict_simape

#DEMANDA cortesía de JAP
# modificada mar2026
def get_demanda_dict(dict_df: dict) -> dict:
    df_barras_xls  = dict_df['barras']    
    df_demanda_xls = dict_df['barradem']
    NDem, data_dem, data_values, barras_cero = parse_demanda(df_barras_xls, df_demanda_xls)
    return {'demanda':{'NDem':NDem,  'DATA1':data_dem.values ,'DATA2':data_values, "DATA3":barras_cero}}

#MANTENIMIENTOS CENTRALES
def get_mant_dict2(dict_df: dict, macro_profile=None):
    nprec = np.finfo(np.float64).precision
    df_mant, df_mant_falla = parse_mancen(dict_df, macro_profile=macro_profile)
    # Umbral de limpieza de potencia residual (MW)
    POT_CLEAN = 0.1
    def _transformar_central(cen: str, df_cen: pd.DataFrame) -> pd.DataFrame:
        """Normaliza y limpia residuos de potencia para el template MANT_TMPL."""
        df_out = df_cen.copy()
        df_out['potmax'] = pd.to_numeric(df_out['potmax'], errors='coerce').fillna(0.0)
        df_out['potmin'] = pd.to_numeric(df_out['potmin'], errors='coerce').fillna(0.0)

        # VBA does not apply a minimum-power cleanup threshold; removed to match VBA output exactly.

        # ERNC stores year-2 blocks as 276-550 to preserve sort order.
        # Map back to 1-275 for the written output (VBA repeats block numbers).
        df_out['bloque'] = ((df_out['bloque'].astype(int) - 1) % 275) + 1

        import math as _math
        from decimal import Decimal, ROUND_HALF_UP
        def _sig_digits(v):
            s = str(float(v)).lstrip('-')
            if 'e' in s or 'E' in s:
                return 20
            s = s.replace('.', '').lstrip('0')
            return len(s)
        def _vba_15sig(fv):
            # VBA Format(x,"0.00"): take exact IEEE 754 decimal, round to 15 sig
            # digits (RHUP), then RHUP to 2dp. The 16th significant digit of the
            # exact decimal determines direction.
            if fv == 0.0:
                return 0.0
            import decimal as _dm
            d = _dm.Decimal(fv)
            ctx = _dm.Context(prec=15, rounding=ROUND_HALF_UP)
            d15 = ctx.create_decimal(d)
            return float(d15.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        def _rhup(v):
            try:
                fv = float(v)
                if _sig_digits(fv) <= 14:
                    return float(Decimal(str(fv)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                # Messy repr: only use 15-sig path if value is BELOW the nearest half-cent
                # (VBA's display precision bumps it to the midpoint → rounds up).
                # If at or above the midpoint, rhup_plain is already correct.
                half = round(fv * 200) / 200
                if fv < half:
                    return _vba_15sig(fv)
                return float(Decimal(str(fv)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except Exception:
                return round(float(v), 2)
        df_out['potmax'] = df_out['potmax'].apply(_rhup)
        df_out['potmin'] = df_out['potmin'].apply(_rhup)
        return df_out
    def _construir_data(df_in: pd.DataFrame, all_cen_names: list) -> dict:
        """Construye el diccionario DATA para el template MANT_TMPL con captura de error a archivo."""
        try:
            data = {"NTOT": len(all_cen_names), "DATA": {}, "CEN": all_cen_names}
            for c in all_cen_names:
                data["DATA"][str(c)] = {"DATA": np.empty((0, 4)), "NMANT": 0, "SUM": 0.0}
            if df_in is None or df_in.empty:
                return data
            
            # CONVERSIÓN TOTAL A LISTA DE DICCIONARIOS PARA EVITAR PANDAS
            # Aseguramos que no hay columnas duplicadas ANTES de convertir
            df_safe = df_in.loc[:, ~df_in.columns.duplicated()].copy()
            records = df_safe.to_dict('records')
            
            # Agrupar nativamente
            cen_map = {}
            for r in records:
                cname = str(r.get('central', ''))
                if not cname: continue
                if cname not in cen_map: cen_map[cname] = []
                cen_map[cname].append(r)
            for cen in all_cen_names:
                cname = str(cen)
                if cname in cen_map:
                    # Usamos listas para construir el DataFrame mínimo
                    m_list = []
                    for r in cen_map[cname]:
                        m_list.append([r.get('Mes'), r.get('bloque'), r.get('potmin'), r.get('potmax')])
                    aux_cen = pd.DataFrame(m_list, columns=["Mes", "bloque", "potmin", "potmax"]).sort_values(by=['bloque'])
                    dd = _transformar_central(cname, aux_cen)
                    data["DATA"][cname] = {
                        "DATA": dd.values,
                        "NMANT": len(dd),
                        "SUM": float(dd['potmax'].sum())
                    }
            return data
        except Exception as e:
            import traceback
            with open("error_traceback.txt", "w") as f:
                traceback.print_exc(file=f)
            print(f"FALLO CRITICO: Ver error_traceback.txt. Error: {e}")
            return {"NTOT": len(all_cen_names), "DATA": {str(c): {"DATA": np.empty((0,4)), "NMANT": 0, "SUM": 0.0} for c in all_cen_names}, "CEN": all_cen_names}

    # Obtener nombres de todas las centrales ACTIVAS (mismo universo que plpcnfce.dat)
    # Importar parse_centrales si no está disponible, o usar lógica equivalente
    from data_parsers import parse_centrales
    embalses, series, pasadas, termicas, fallas, baterias, ncen = parse_centrales(dict_df['centrales'], False)

    # mantcen incluye Embalses, Series, Pasadas, Térmicas, Baterías 
    def _vba_sort_key(name):
        # Replica el orden de Excel/VBA: '_' ordena antes de letras, '-' ordena después
        return name.replace('_', chr(0)).replace('-', chr(255)).upper()

    cen_names_main  = []
    for df_aux in [embalses, series, pasadas, termicas, baterias]:
        if not df_aux.empty:
            cen_names_main.extend(df_aux['central'].astype(str).str.strip().tolist())
    cen_names_main = sorted(cen_names_main, key=_vba_sort_key)

    cen_names_falla = []
    if not fallas.empty:
        cen_names_falla = fallas['central'].astype(str).str.strip().tolist()

    mantcen_raw      = _construir_data(df_mant,       cen_names_main)
    mantcen_falla_raw = _construir_data(df_mant_falla, cen_names_falla)

    # Filtrar centrales sin datos de mantenimiento (NMANT=0) igual que el modelo VBA
    active_main  = [c for c in mantcen_raw['CEN']       if mantcen_raw['DATA'][c]['NMANT'] > 0]
    active_falla = [c for c in mantcen_falla_raw['CEN'] if mantcen_falla_raw['DATA'][c]['NMANT'] > 0]

    mantcen_raw['CEN']       = active_main
    mantcen_raw['NTOT']      = len(active_main)
    mantcen_falla_raw['CEN']  = active_falla
    mantcen_falla_raw['NTOT'] = len(active_falla)

    return {
        'mantcen'       : mantcen_raw,
        'mantcen_falla' : mantcen_falla_raw,
    }
