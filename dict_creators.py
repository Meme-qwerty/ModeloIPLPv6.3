# archivo de funciones que generan los diccionarios de datos a partir de los dataframes
import pandas as pd
import math
from decimal import Decimal, ROUND_HALF_UP

from contenedores_auxiliares import TAGS_LAJA, TAGS_MAULE
from data_parsers import *
from utils import *


###############################################################################
####### ETAPAS
def get_etapas_dict(dict_df: dict) -> dict:
    
    df_etapas_xls = dict_df['etapas']
    
    df_etapas = parse_etapas(df_etapas_xls)
    
    dict_eta = {'etapas': {
                       'NETAPAS': len(df_etapas),
                       'DATA'  : df_etapas.values
                      }}
    return dict_eta

###############################################################################
####### BLOQUES
def get_bloques_dict(dict_df: dict) -> dict:
    
    df_blodem_xls = dict_df['blodem']
    
    df_blo = parse_bloques(df_blodem_xls)
    
    MES_MESC = {4:1,5:2,6:3,7:4,8:5,9:6,10:7,11:8, 12:9, 1:10, 2:11, 3:12}
    
    #df_blo["Mes"] = df_blo["Mes"].apply(lambda x: MES_MESC[x])
    
    dict_blo = {'bloques':{'NBLO': int(df_blo["indice"].max()),
                      'DATA': df_blo.values}}

    return dict_blo

###############################################################################
####### BARRAS
def get_barras_dict(dict_df: dict) -> dict:
    
    df_barras_xls = dict_df['barras']
    
    df_barras = parse_barras(df_barras_xls)
    
    dict_bar = {'barras': {'NBARRAS': len(df_barras), 'BNAMES': df_barras["BARRA"].values.tolist()}}
    
    return dict_bar

###############################################################################
####### LINEAS

# editado may2025
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

###############################################################################
####### EXTRACCIONES
def get_extrac_dict(dict_df: dict) -> dict:
    
    df_extracciones_xls = dict_df['Extracciones']
    
    df_extr = parse_extracciones(df_extracciones_xls)
    
    dict_extr = { 'extracciones': {
                 'NCEN': len(df_extr),
                 'DATA': df_extr.values}
    }

    return dict_extr

###############################################################################
####### RENDIMIENTOS
def get_cerend_dict(dict_df: dict) -> dict:
    
    df_rendimientos_xls = dict_df['Rendimientos']
    df_centrales_xls    = dict_df['centrales']
    
    df_rend = parse_rendimientos(df_rendimientos_xls, df_centrales_xls)
    
    dict_rend = {'rendimientos': {
                'NEMB': len(df_rend['central'].unique().tolist()),
                'DATA': df_rend.values}
    }
    
    return dict_rend
###############################################################################
####### FILTRACIONES
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
###############################################################################
####### REBALSES
def get_rebemb_dict(dict_df: dict) -> dict:
    
    df_rebalses_xls = dict_df['Rebalse']
    
    df_reb = parse_rebalses(df_rebalses_xls)
    
    dict_reb = {'rebalses':{'NEMB': len(df_reb), 
                       'DATA'  : df_reb.values}}
    
    return dict_reb

###############################################################################
####### BATERIAS
def get_cenbat_dict(dict_df: dict) -> dict:

    df_bat_xls = dict_df['Baterias']

    df_bat = parse_baterias(df_bat_xls)

    data = [
        (int(row['INDICE']),
         str(row['BATERIAS']).strip(),
         int(row['Conectada a la Barra']),
         float(row['Rendimiento de Descarga']),
         float(row['Mínima']),
         float(row['Máxima']),
         str(row['Central de Carga']),
         float(row['Rendimiento de Carga']))
        for _, row in df_bat.iterrows()
    ]

    return {'cenbat': {'NBAT': len(data), 'MAXINJ': 1, 'DATA': data}}

###############################################################################
####### CENPMAX
def get_cepmax_dict(dict_df: dict) -> dict:
    
    df_cenpmax_xls = dict_df['CenPmax']
    
    df_aux, df_aux2, embnames = parse_cenpmax(df_cenpmax_xls)
    
    dict_cpmax = { 'cenpmax': {
                 'NEMB' : len(embnames),
                 'fixed': df_aux.values,
                 'DATA' :{name: df_aux2.loc[name, :].values for name in embnames}}             
    }
    
    return dict_cpmax
###############################################################################
####### LAJA
# modificado temporalmente -> ago2025
def get_lajam_dict(dict_df: dict, tags: dict = TAGS_LAJA) -> dict:
    
    df_laja_xls = dict_df['LAJAM']
    
    out = {'laja': {}}
    for index, row in df_laja_xls.iterrows():
        if index > 39: continue
        name, typ, coerce = tags[index]
        if not name: continue
        #print(name, typ, coerce, row)
        if typ:
            n = int(row.iloc[2])
            value = list(map(coerce, row.iloc[3:(3+n)].to_list()))
        else:
            try:
                value = coerce(row.iloc[3])
                if type(value) != str:
                    if math.isnan(value):
                        value = coerce(row.iloc[2])
                else:
                    if value == 'nan':
                        value = ''
            except ValueError:
                value = coerce(row.iloc[2])
        
        out['laja'][name] = value
    
    # machucon temporal ago2025
    out['laja']['RetManRiegEtaRet'] = 0.0
    out['laja']['QRet'] = [0.0]
    out['laja']['NumEtaQForz'] = 0
    out['laja']['QForzToro'] = 0
        
    return out
###############################################################################
####### MAULE
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
    
    #machucon
    out['maule']['PorRet'] = [str(por) for por in out['maule']['PorRet']]
    return out
###############################################################################
####### CENTRALES
# editado may2025
def get_cnfcen_dict(dict_df: dict, uninodal: bool = False) -> dict:
    
    df_centrales_xls = dict_df['centrales']
    
    embalses, series, pasadas, termicas, fallas, baterias, ncen = parse_centrales(df_centrales_xls, uninodal)
    
    embalses['FEsc'] = embalses.FEsc.astype(str).apply(lambda x: "1.0E+{}".format(x.count('0')))
    termicas[['vertmin', 'vertmax']] = termicas[['vertmin', 'vertmax']].replace(np.nan, 0.0)
    baterias[['vertmin', 'vertmax']] = baterias[['vertmin', 'vertmax']].replace(np.nan, 0.0)
    
    termicas  = correccion_preredondeo(termicas, ['potmax'], 1)
    series    = correccion_preredondeo(series, ['potmax'], 1)
    pasadas   = correccion_preredondeo(pasadas, ['potmax'], 1)
    fallas    = correccion_preredondeo(fallas, ['potmax'], 1)
    embalses  = correccion_preredondeo(embalses, ['potmax'], 1)
    baterias  = correccion_preredondeo(baterias, ['potmax'], 1)
    
    dict_cen = {'centrales':{'NCEN': ncen, 
                         'NEMB': len(embalses),
                         'NSER': len(series),
                         'NFALLA': len(fallas),
                         'NPAS': len(pasadas),
                         'NBAT': len(baterias),
                         'EMBALSES': embalses.values,
                         'SERIES': series.values,
                         'TERMICAS': termicas.values,
                         'PASADAS': pasadas.values,
                         'BATERIAS': baterias.values}}

    return dict_cen

###############################################################################
####### PLEM1

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

###############################################################################
####### AFLUENTES

def get_aflce_dict( dict_df : dict,
                    sim_type  : TipoSimulacion,
                    afl4s: bool  = True) -> dict:
    
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
    
    
###############################################################################
####### COSTOS

def get_cosce_dict( dict_df: dict) -> dict:
    
    df_cos_xls = dict_df['cvariable'] # hoja costos
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    
    
    NFil, dict_CVarEta, CenNomFinal, NEtaCen, dict_MantCen, IMant, imes_aux = parse_costos(df_cos_xls, df_eta_xls, df_cen_xls)
    
    dict_cosce = {'cosce': {"NFIL": NFil, "CVARETA": dict_CVarEta, "DATA": zip(CenNomFinal, NEtaCen), "MANTCEN": dict_MantCen, "IMANT": IMant, "IMES": imes_aux}}
    
    return dict_cosce

###############################################################################
####### MANTENIMIENTOS EMBALSES

def get_manem_dict( dict_df: dict) -> dict :
    
    
    df_emb_xls = dict_df['MantEMB']   # hoja costos
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    
    my_dict, NEmb = parse_embalses(df_emb_xls, df_eta_xls, df_cen_xls)
    
    dict_mantemb = {'mantemb': {'DATA': my_dict, 'NEMB': NEmb}}
    
    return dict_mantemb

###############################################################################
####### MANTENIMIENTOS EMBALSES H

def get_manemh_dict(dict_df: dict) -> dict :
    
    
    df_emh_xls = dict_df['MantEMBh']  # hoja costos
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    
    NMantEmbMant, MantCen, df_eta, VMinEta, CostoEta = parse_embalsesh(df_emh_xls, df_eta_xls, df_cen_xls)
    
    dict_manemh  = {'manemh': {ename: 
                           {'NMANT': value, 
                            'DATA': np.column_stack((df_eta.loc[MantCen[ename],"Etapa"].values, 
                                                     VMinEta.loc[MantCen[ename], ename].values, 
                                                     CostoEta.loc[MantCen[ename], ename].values ))} for ename, value in NMantEmbMant.items()}}
    
    return dict_manemh

###############################################################################
####### MANTENIMIENTOS LINEAS

# modificado jul2025
def get_manli_dict( dict_df: dict) -> dict :
    
    df_lin_xls = dict_df['lineas']    # hoja lineas
    df_mli_xls = dict_df['manLin']    # hoja mantli
    df_eta_xls = dict_df['etapas']    # hoja etapas
    df_cen_xls = dict_df['centrales'] # hoja centrales
    df_ml2_xls = dict_df['manLin2']   # datos adicionales
    
    
    
    data_dict, mant_unique, mant_nblo, nmant = parse_mlineas(df_lin_xls, df_mli_xls, df_eta_xls, df_cen_xls, df_ml2_xls)
    
    dict_mantlin =  {'mantlin': {"DATA": data_dict, "LINEAS": zip(mant_unique, mant_nblo), "NMANT": nmant}}
    
    return dict_mantlin

###############################################################################
####### SIMULACIONES Y APERTURAS

def get_simape_dict(dict_df   : dict,    
                    sim_type  : TipoSimulacion,  # 'flag' de tipo simulacion
                    ale_type  : TipoAleatorio,   # 'flag' de tipo de aleatoriedad
                    si2_type  : TipoSimulacion2, # 'flag' de tipo de simluacion 2 (hist o aleat)
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

###############################################################################
####### DEMANDA cortesía de JAP
# modificada ene2025
def get_demanda_dict(dict_df: dict) -> dict:
    
    df_barras_xls  = dict_df['barras']    
    df_demanda_xls = dict_df['barradem']
   
    NDem, data_dem, data_values, barras_cero = parse_demanda(df_barras_xls, df_demanda_xls)

    return {'demanda':{'NDem':NDem,  'DATA1':data_dem.values ,'DATA2':data_values, "DATA3":barras_cero}}

###############################################################################
####### MANTENIMIENTOS CENTRALES
# modificado feb2025
def get_mant_dict2(dict_df: dict):
    nprec                  = np.finfo(np.float64).precision
    df_mant, df_mant_falla = parse_mancen(dict_df)
    aux                    = df_mant.sort_values(by = ['central', 'bloque'])
    #aux2                   = aux.copy()
    aux[['int','dec']] = aux['potmax'].round(nprec-3).astype(str).str.split(".", expand = True)
    aux['ndec'] = aux['dec'].str.len()
    mask = (aux.ndec == 3) & (aux.dec.str.endswith("5"))
    aux.loc[mask, 'potmax'] = (aux.loc[mask, 'potmax'] + 0.001)
    aux['potmax']          = aux['potmax'].round(2)
     
    aux_falla              = df_mant_falla.sort_values(by = ['central', 'bloque'])
    #auxf                   = aux_falla.copy()
    aux_falla[['int','dec']] = aux_falla['potmax'].round(nprec-3).astype(str).str.split(".", expand = True)
    aux_falla['ndec'] = aux_falla['dec'].str.len()
    
    mask = (aux_falla.ndec == 3) & (aux_falla.dec.str.endswith("5"))
    aux_falla.loc[mask, 'potmax']  = (aux_falla.loc[mask, 'potmax'] + 0.001)
    aux['potmax']          = aux['potmax'].round(2)
     
    centrales              = aux.central.unique()
    centrales_falla        = aux_falla.central.unique()
    data                   = {"NTOT": len(centrales), "DATA": {}, "CEN": centrales}
    data_falla             = {"NTOT": len(centrales_falla), "DATA": {}, "CEN": centrales_falla}
    for cen in centrales:
        aux_cen = aux[aux.central == cen]
        data["DATA"][cen] = {}
        dd = aux_cen[["Mes", "bloque", "potmin", "potmax"]]
        data["DATA"][cen]["DATA"] = dd.values
        data["DATA"][cen]["NMANT"] = len(dd)
        data["DATA"][cen]["SUM"] = dd['potmax'].sum()
        
    for cen in centrales_falla:
        aux_cen = aux_falla[aux_falla.central == cen]
        data_falla["DATA"][cen] = {}
        dd = aux_cen[["Mes", "bloque", "potmin", "potmax"]]
        data_falla["DATA"][cen]["DATA"] = dd.values
        data_falla["DATA"][cen]["NMANT"] = len(dd)
        data_falla["DATA"][cen]["SUM"] = dd['potmax'].sum()
        
    out_dict = {'mantcen': data, 'mantcen_falla': data_falla}
    return out_dict
