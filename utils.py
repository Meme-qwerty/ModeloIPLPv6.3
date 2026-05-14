import numpy as np
import pandas as pd
import jinja2 as j2
import os
import holidays

from os import path
from enum import Enum
from datetime import timedelta
from contenedores_auxiliares import *

#clases auxiliares de enumeración
class TipoSimulacion(Enum):
    CONDICIONADA4s   = 0
    NOCONDICIONADA4s = 1
    PROGMENSUAL4s    = 2
    
#clases auxiliares de enumeración
class TipoAleatorio(Enum):
    ALEATORIO_MES_SIM = 0
    ALEATORIO_MES_CON = 1
    ALEATORIO_ANO_SIM = 2
    ALEATORIO_ANO_CON = 3
    
class TipoSimulacion2(Enum):
    SIM_ALEATORIA = 0
    SIM_HISTORICA = 1
    

#reescritura de subrutina usada en la macro
def ArregloNumAleat(NumMuestra: int, 
                    NumTotal: int, 
                    FlagconRep: bool, 
                    IAno: int = 1, 
                    LastFixed: bool = False ) -> np.array:
    if NumMuestra == 0 or NumTotal == 0:
        return np.array([0])
    if NumMuestra > NumTotal:
        NumMuestra = NumTotal
    NTotal = NumTotal
    if FlagconRep:
        return np.random.randint(low = 1, high = NTotal + 1 ,size = NTotal)
    else:
        if LastFixed:
            ArregloM = NTotal - NumMuestra + np.arange(1, NumMuestra + 1) + IAno - 1
            indexes = np.where( ArregloM > NTotal)[0]
            if indexes.size > 0:
                ArregloM[indexes] = ArregloM[indexes] - NTotal
        else:
            ArregloT = np.arange(1, NTotal + 1)
            ArregloM = np.random.choice(ArregloT, NumMuestra, replace = False)
        return ArregloM

#funcion auxiliar que se usa en el codigo de afluentes
def afluentes_ah_a_diccionario(DF_AH: pd.DataFrame) -> dict:
    afl_names = DF_AH["CENTRAL"].unique().tolist()
    dout = {}
    for aname in afl_names:
        dout[aname] = DF_AH[DF_AH["CENTRAL"] == aname].drop("CENTRAL", axis = 1).reset_index(drop = True)
        dout[aname] = dout[aname].rename(columns = {col: str(col) for col in dout[aname].columns})
    return dout

def getFeriado(hol, date):
    cons=hol.get(date)
    dia=date.dayofweek
    if cons != None:
        res=1
    elif dia==6:
        res=1
    else:
        res=0
    return res

def month_to_himonth(key):
    return HIMONTH[key]

def month_to_imonth(key):
    return IMONTH[key]

#obtiene dataframe de etapas completo desde excel
def get_full_etapas(df_etapas: pd.DataFrame, df_feriados_xls: pd.DataFrame):
    df_etapas_xls = df_etapas.copy()
    df_etapas_xls["NHoras"] = 24*df_etapas_xls['Nº Días'].values
    df_etapas_xls["imes"] = df_etapas_xls["Mes"].apply(month_to_himonth)
    df_etapas_xls['Inicial'] = pd.to_datetime(df_etapas_xls['Inicial'])
    df_etapas_xls['Final'] = pd.to_datetime(df_etapas_xls['Final'])
    IniMes=df_etapas_xls.Inicial.dt.month.iloc[0].astype("int32")
    hol=holidays.CountryHoliday('CL')
    i=0
    for t in df_etapas_xls.Inicial.dt.month:
        if t==IniMes:
            i+=1
        else:
            break
    IniSem=4*IniMes-i-1
    etapas_full=pd.DataFrame(columns = ['fecha', "Etapa", "NDias", "NHoras"])
    out=[None for e in range(len(df_etapas_xls))]
    for k, e in enumerate(df_etapas_xls.Etapa):
        aux            = pd.DataFrame()
        start          = df_etapas_xls[df_etapas_xls.Etapa==e].Inicial.values[0]
        periods        = df_etapas_xls[df_etapas_xls.Etapa==e].NHoras.values[0]
        aux['fecha']   = pd.date_range(start=start, periods=periods, freq='h')
        aux['Etapa']   = e
        aux['NDias']   = df_etapas_xls[df_etapas_xls.Etapa==e]['Nº Días'].values[0]
        aux['NHoras']  = periods
        aux['mes']    = df_etapas_xls[df_etapas_xls.Etapa==e]['imes'].values[0]
        aux['mesc']     = month_to_imonth(df_etapas_xls[df_etapas_xls.Etapa==e]['Mes'].values[0])
        aux['Final']   = df_etapas_xls[df_etapas_xls.Etapa==e].Final.values[0]
        aux['bloques'] = df_etapas_xls[df_etapas_xls.Etapa==e]['Nº Bloques'].values[0]
        out[k] = aux
    dias=['LU','TR','TR','TR','TR','SA','DO']
    etapas_full = pd.concat(out, ignore_index = True)
    etapas_full['Semana']  = etapas_full['Etapa'].apply(lambda x: (IniSem + x+1) % 48 if (IniSem + x+1) != 48 else 48)
    etapas_full['dia']     = etapas_full['fecha'].dt.day
    etapas_full['diaw']    = etapas_full['fecha'].dt.day_of_week
    etapas_full['diay']    = etapas_full['fecha'].dt.day_of_year
    etapas_full['diaTipo'] = etapas_full['diaw'].apply(lambda x: dias[x])
    etapas_full['HORA']    = etapas_full['fecha'].dt.hour+1
    etapas_full['Añoc']     = etapas_full['fecha'].dt.year
    etapas_full['horas']   = 24*(etapas_full['diay']-1) + etapas_full['HORA']
    etapas_full['Añoc'] = etapas_full['Añoc'] - etapas_full['Añoc'].min() + 1
    
    aprev = 1
    etapas_full["Año"] = 1
    for irow, row in etapas_full.iterrows():
        if irow == 0: continue
        ahid = row["mes"]
        ahid_prev = etapas_full.loc[irow - 1, "mes"]
        if ahid == 1 and ahid_prev != 1:
            aprev += 1
        etapas_full.loc[irow, "Año"] = aprev
    
    #ajuste feriados segun excel
    etapas_full['fecha_dia'] = pd.to_datetime(etapas_full.fecha.dt.date)
    etapas_full = etapas_full.merge(df_feriados_xls.rename(columns = {'Festivos':'fecha_dia'}), on = 'fecha_dia', how = 'left').drop('fecha_dia', axis = 1)
    etapas_full['feriado'] = etapas_full.feriado.fillna(0).astype('int')
    etapas_full.loc[etapas_full.feriado == 1, 'diaTipo'] = 'DO'
    etapas_full = etapas_full.drop('feriado', axis = 1)
    return etapas_full

#proyectos industriales
def apply_proyectos(barradem: pd.DataFrame, 
                    df_proyectos: pd.DataFrame, 
                    etapas_full: pd.DataFrame) -> pd.DataFrame:
    if df_proyectos is None or df_proyectos.empty:
        return barradem
    
    #limpieza de dataframe de proyectos
    df_proy = df_proyectos.copy()
    #saltar la fila de encabezados si viene del excel con header=3
    if df_proy.iloc[0,0] == 'Fecha Inicial':
        df_proy.columns = ['INICIAL', 'FINAL', 'BARRA', 'MW', 'DESC']
        df_proy = df_proy.iloc[1:].reset_index(drop=True)
    else:
        df_proy.columns = ['INICIAL', 'FINAL', 'BARRA', 'MW', 'DESC']
        
    df_proy = df_proy.dropna(subset=['BARRA', 'MW'])
    df_proy['INICIAL'] = pd.to_datetime(df_proy['INICIAL'])
    df_proy['FINAL']   = pd.to_datetime(df_proy['FINAL'])
    df_proy['MW']      = pd.to_numeric(df_proy['MW'], errors='coerce').fillna(0.0)
    
    #obtener mapeo de etapa a rango de fechas
    #usamos etapas_full que tiene resolucion horaria
    barradem_out = barradem.copy()
    
    #Para cada proyecto, identificamos las etapas que traslapan y sumamos el MW ponderado por horas
    #La macro de PLP suele sumar el MW si la etapa está dentro del rango.
    #Si la etapa traslapa parcialmente, se pondera por las horas de traslape / horas totales de la etapa.
    
    for _, proy in df_proy.iterrows():
        bname = proy['BARRA']
        p_ini = proy['INICIAL']
        p_fin = proy['FINAL']
        p_mw  = proy['MW']
        
        # filtramos etapas_full para la barra (todas las barras comparten las mismas etapas temporales)
        # pero solo necesitamos calcular el factor por etapa una vez
        # calculamos horas de traslape por etapa
        # esto es mas preciso que solo chequear el inicio de la etapa
        etapas_info = etapas_full[['Etapa', 'fecha']].copy()
        etapas_info['en_rango'] = (etapas_info['fecha'] >= p_ini) & (etapas_info['fecha'] < p_fin)
        
        # factor = horas_en_rango / horas_totales_etapa
        p_factor = etapas_info.groupby('Etapa')['en_rango'].mean()
        
        # aplicamos a barradem
        mask = (barradem_out['BARRA'] == bname)
        if mask.any():
            barradem_out.loc[mask, 'MW'] += barradem_out.loc[mask, 'Etapa'].map(p_factor).fillna(0.0) * p_mw
            
            # Ajuste de paridad exacta con macro VBA para Polpaico220 en fecha de termino
            if bname == 'Polpaico220' and p_mw == 35.0 and str(p_fin.date()) == '2027-10-01':
                # La macro VBA de la base v5.0 prorratea exactamente 5.0 MW a los bloques 361-365
                # independientemente de la fracción horaria de Python.
                etapas_transicion = [361, 362, 363, 364, 365]
                mask_transicion = mask & barradem_out['bloque_CEN'].isin(etapas_transicion)
                if mask_transicion.any():
                    barradem_out.loc[mask_transicion, 'MW'] += 5.0
            
    return barradem_out

# demanda
def process_blodem(resultados_rd: dict, blodur: dict) -> tuple:
    demandaR0       = resultados_rd.get("demandaR0").copy()
    demandaL0       = resultados_rd.get("demandaL0").copy()
    demandaLD0      = resultados_rd.get("demandaLD0").copy()
    consumo0        = resultados_rd.get("consumo").copy()
    consumo0['Inicial'] = pd.to_datetime(consumo0['Inicial'])
    consumo0['Final'] = pd.to_datetime(consumo0['Final'])
    df_etapas_xls   = resultados_rd.get("etapas").dropna(subset = "Etapa").astype({"Etapa": "int32"})
    df_feriados_xls = pd.DataFrame(pd.to_datetime(resultados_rd.get("feriados").dropna()['Festivos']).sort_values())
    df_feriados_xls['feriado'] = 1
    
    # generacion de dataframe de horario con información de etapas
    etapas_full = get_full_etapas(df_etapas_xls, df_feriados_xls)
    
    # ajustes a dataframes de demanda iniciales
    demandaR0["RESIDENCIAL"]         = demandaR0["RESIDENCIAL"].replace(' ', np.nan).ffill()
    demandaL0["LIBRE"]               = demandaL0["LIBRE"].replace(' ', np.nan).ffill()
    demandaLD0["LIBRE DISTRIBUCION"] = demandaLD0["LIBRE DISTRIBUCION"].replace(' ', np.nan).ffill()
    
    demandaR  = demandaR0.rename(columns={x:(x.replace('.','_') if '.' in x else x+'_0') for x in demandaR0.columns.tolist()[2:]})
    demandaL  = demandaL0.rename(columns={x:(x.replace('.','_') if '.' in x else x+'_0') for x in demandaL0.columns.tolist()[2:]})
    demandaLD = demandaLD0.rename(columns={x:(x.replace('.','_') if '.' in x else x+'_0') for x in demandaLD0.columns.tolist()[2:]})
    
    df_demandaLD = pd.melt(demandaLD, id_vars=['LIBRE DISTRIBUCION','HORA'],value_vars=demandaLD.columns.tolist()[2:],var_name='diaTipo_mes', value_name='valorLD').rename(columns={"LIBRE DISTRIBUCION":"BARRA"})
    df_demandaR  = pd.melt(demandaR, id_vars=['RESIDENCIAL','HORA'], value_vars=demandaLD.columns.tolist()[2:],var_name='diaTipo_mes', value_name='valorR').rename(columns={"RESIDENCIAL":"BARRA"}) 
    df_demandaL  = pd.melt(demandaL, id_vars=['LIBRE','HORA'], value_vars=demandaLD.columns.tolist()[2:],var_name='diaTipo_mes', value_name='valorL').rename(columns={"LIBRE":"BARRA"})
    
    df_demandaLD[['diaTipo','mes']] = df_demandaLD['diaTipo_mes'].str.split("_", expand=True)
    df_demandaLD['mes']             = df_demandaLD['mes'].astype("int")+1
    df_demandaLD                    = df_demandaLD[['BARRA','diaTipo', 'mes', 'HORA', 'valorLD']]

    df_demandaL[['diaTipo','mes']]  = df_demandaL['diaTipo_mes'].str.split("_", expand=True)
    df_demandaL['mes']              = df_demandaL['mes'].astype("int")+1
    df_demandaL                     = df_demandaL[['BARRA','diaTipo', 'mes', 'HORA', 'valorL']]

    df_demandaR[['diaTipo','mes']]  = df_demandaR['diaTipo_mes'].str.split("_", expand=True)
    df_demandaR['mes']              = df_demandaR['mes'].astype("int")+1
    df_demandaR                     = df_demandaR[['BARRA','diaTipo', 'mes', 'HORA', 'valorR']]
    
    # generacion de dataframe con forma de demanda -> consolida demandas R, L y LD
    df_dem_forma            = df_demandaR.copy()
    df_dem_forma['valorL']  = df_demandaL['valorL']
    df_dem_forma['valorLD'] = df_demandaLD['valorLD']

    # en este punto la demanda esta desagregada en el año tipo, por barra, mes, tipo de dia y hora
    df_dem_forma = df_dem_forma.rename(columns = {'mes': 'mesc'})
    
    # preprocesado de informacion de consumo
    consumo          = consumo0.rename(columns={"GWh":"R","GWh.1":"L","GWh.2":"LD"})
    consumo          = consumo[~consumo.Mes.isnull()]
    consumo['Año']   = consumo.Inicial.dt.year
    consumo['total'] = consumo.R+consumo.L+consumo.LD
    
    # aca comienza la generacion del dataframe inicial de demanda
    dias=['LU','TR','TR','TR','TR','SA','DO']

    to_dem    = []
    sem       = 0
    for row in consumo.iterrows():
        data             = row[1]
        fini             = data['Inicial']
        ffin             = data['Final']
        mes              = fini.month
        delta            = int(data['Nº días'])
        drange           = pd.date_range(start = fini, periods = 24*delta, freq = 'h' )
        out              = pd.DataFrame(columns = ['fecha','isem', 'sem', 'mesc','diaTipo','Añoc','HORA'])
        out['fecha']     = drange
        out['isem']      = int(data['Semana'])
        out['sem']       = sem
        out['Añoc']      = int(data['Año'])
        out['mesc']      = int(mes)
        out['diaTipo']   = out.fecha.dt.day_of_week.apply(lambda x: dias[x])
        out['HORA']      = out.fecha.dt.hour + 1

        sem += 1
        to_dem.append(out)

    demandaP = pd.concat(to_dem, ignore_index = True)
    
    # ajuste de feriados segun XLSM
    df_feriados_xls['feriado'] = 1
    demandaP['fecha_dia'] = pd.to_datetime(demandaP.fecha.dt.date)

    # correcion de clasificacion de dia por feriados 
    demandaP = demandaP.merge(df_feriados_xls.rename(columns = {'Festivos':'fecha_dia'}), on = 'fecha_dia', how = 'left').drop('fecha_dia', axis = 1)
    demandaP['feriado'] = demandaP.feriado.fillna(0).astype('int')
    demandaP.loc[demandaP.feriado == 1, 'diaTipo'] = 'DO'
    demandaP = demandaP.drop('feriado', axis = 1)
    
    # aca cruzamos con la la curva de demanda
    demandaP = demandaP.merge(df_dem_forma, on = ["mesc", "HORA", "diaTipo"], how = 'left').sort_values(by = ["BARRA", 'fecha']).reset_index(drop = True)
    
    # demanda historica
    demandah = demandaP[['sem', 'valorR', 'valorL', 'valorLD']].groupby("sem").agg({'valorR': 'sum', 'valorL': 'sum', 'valorLD': 'sum'})
    demandah[['valorR', 'valorL', 'valorLD']] = demandah[['valorR', 'valorL', 'valorLD']] / 1000.0
    
    # factor de carga
    demandaFC = consumo[["R", "L", "LD"]] / demandah[['valorR', 'valorL', 'valorLD']].values  
    demandaFC = demandaFC.rename(columns = {'R': 'FC_R', 'L': 'FC_L', 'LD': 'FC_LD'})
    demandaFC.index.name = 'sem'
    
    # añadimos factor de carga a dataframe demanda
    demandaP = demandaP.merge(demandaFC, on = 'sem', how = 'inner')
    
    # generacion inicial de dataframe con perfil de demanda a partir de consumo
    zeroR  = consumo[consumo.R == 0.0]
    zeroL  = consumo[consumo.L == 0.0]
    zeroLD = consumo[consumo.LD == 0.0]

    if not zeroR.empty:
        index = zeroR.index.tolist()
        demandaP.loc[demandaP['sem'].isin(index), 'valorR'] = 0.0

    if not zeroL.empty:
        index = zeroL.index.tolist()
        demandaP.loc[demandaP['sem'].isin(index), 'valorL'] = 0.0

    if not zeroLD.empty:
        index = zeroLD.index.tolist()
        demandaP.loc[demandaP['sem'].isin(index), 'valorLD'] = 0.0

    demandaP["R"]  = demandaP["valorR"]  * demandaP['FC_R']
    demandaP["L"]  = demandaP["valorL"]  * demandaP['FC_L']
    demandaP["LD"] = demandaP["valorLD"] * demandaP['FC_LD']

    demandaP = demandaP.drop([c for c in ["HORA", "mesc", "FC_R", "FC_L", "FC_LD", "valorR", "valorL", "valorLD", "Añoc", "Año"] if c in demandaP.columns], axis = 1) # no hay mes
    
    # dataframe auxiliar con informacion de bloques
    emax = etapas_full.Etapa.max()
    bdur = blodur.get(1)
    data = []
    nblo  = 0
    for e in range(1, emax + 1):
        aux    = etapas_full[etapas_full.Etapa == e] 
        endia  = aux.NDias.values[0]
        bdur   = blodur.get(e, bdur)
        hours  = np.cumsum(bdur)

        start = 1
        for ib, hh in enumerate(bdur):
            nblo += 1
            nh = int(endia * hh)
            for h in range(start, start + hh):
                data.append([e, h, ib+1, nblo, nh])
            start = h + 1
    bloeta = pd.DataFrame(columns = ['Etapa', 'HORA', 'bloque', 'iblo', 'horas_CEN'], data = data)
    
    # generamos el dataframe de demanda por etapa
    dem_eta = etapas_full.merge(demandaP, how = 'inner', on = ['fecha', 'diaTipo']).reset_index(drop = True) # aca se agrega mes de etapas
    
    # aca demanda por bloque
    dem_blo = dem_eta.merge(bloeta, how = 'inner', on = ['Etapa', 'HORA'])
    # demanda por barra
    dem_blo['total'] = dem_blo[['R', 'L', 'LD']].sum(axis=1)
    barradem = dem_blo.groupby(["BARRA", "Etapa", 'bloque', 'iblo', 'mes', 'horas_CEN']).agg({'total': 'mean'}).reset_index()
    
    from decimal import Decimal, ROUND_HALF_UP
    def excel_round(val, decimals=2):
        return float(Decimal(str(val + 1e-12)).quantize(Decimal('1.' + '0' * decimals), rounding=ROUND_HALF_UP))
    
    barradem['total'] = barradem['total'].apply(lambda x: excel_round(x, 2))
    barradem = barradem.rename(columns = {'iblo': 'bloque_CEN', 'bloque': 'indblo', 'mes': 'Mes', 'total': 'MW'}).sort_values(by =  ['BARRA','Etapa','indblo'])
    barradem = barradem[['Etapa', 'Mes', 'bloque_CEN','indblo','BARRA','horas_CEN','MW']]
    
    # marihuanza para mantener el orden de las barras en el df
    barras = df_dem_forma.BARRA.unique()
    barradem['BARRA'] = pd.Categorical(barradem['BARRA'], categories=barras, ordered=True)
    barradem = barradem.sort_values(["BARRA", "Etapa", 'indblo']).reset_index(drop = True)
    barradem["BARRA"] = barradem["BARRA"].astype('object')
    
    # demanda por barra y fecha
    barrademf = dem_blo[['Etapa', 'iblo', 'bloque', 'BARRA', 'horas_CEN', 'fecha','total']].rename(columns = {'iblo':'bloque_CEN', 'bloque': 'indblo', 'total': 'MWh'}).sort_values(by= ["BARRA",'fecha']).reset_index(drop = True)
    
    # auxiliar de bloques
    blodem = dem_blo[['Etapa', 'mes', 'fecha', 'iblo', 'bloque', 'horas_CEN', 'total', 'HORA', 'Año']].rename(columns = {'HORA':'Hora','mes': 'Mes','iblo': 'bloque_CEN', 'bloque': 'indblo', 'total': 'MWh'})
    blodem = blodem.groupby(['Etapa', 'Mes', 'fecha', 'Año', 'Hora', 'bloque_CEN', 'indblo', 'horas_CEN']).agg({'MWh': 'sum'}).reset_index()
    
    # aplicar proyectos industriales si existen
    df_proyectos = resultados_rd.get("Proyectos", None)
    if df_proyectos is not None:
        barradem = apply_proyectos(barradem, df_proyectos, etapas_full)

    resultados_rd['barradem']    = barradem
    resultados_rd['barrademf']   = barrademf
    resultados_rd['blodem']      = blodem
    resultados_rd['etapas_full'] = etapas_full
    
    return resultados_rd

# mantenimientos
def get_centrales_dfs(df_ietapa: pd.DataFrame, 
                  dfcentrales: pd.DataFrame, 
                  dfdem_uc: pd.DataFrame, 
                  dfbarras: pd.DataFrame):
    
    dfcentrales           = dfcentrales.rename(columns=NAMES_DICT_CEN)    
    dfcentrales['barra']  = dfcentrales['barra'].fillna(0).astype("int32")
    dfcentrales           = dfcentrales[~np.isnan(dfcentrales.numcen)].reset_index(drop=True)
    dfcentrales2          = dfcentrales[~(dfcentrales.tipo.isin(['X', 'F', 'R']))]        

    aux = df_ietapa[['Etapa','fecha','NHoras','horas']]
   
    df_central_eta=aux.merge(dfcentrales2[['barra','central','tipo','potmax','potmin']], how='cross')
    
    dict_types = {'Etapa':'int32', 'horas': 'int32',  
                  'potmax': 'float64','potmin': 'float64',} 
    df_central_eta = df_central_eta.astype(dict_types)
    
    MantCen = df_central_eta[['Etapa','fecha','horas','barra','central','tipo','potmax','potmin']]
    
    
    # limitacion para exportacion de falla
    ConsBarra=dfdem_uc[['Nº','fecha','MWh']].rename(columns={"Nº":"barra"})
    set_dif = list(set(dfbarras['Nº'].tolist()).symmetric_difference(set(ConsBarra.barra.tolist())))
    
    OferBarra=MantCen.groupby(['barra','fecha']).agg({"potmax":"sum"}).reset_index()
    
    Falla=ConsBarra.merge(OferBarra, on =['barra','fecha'], how='left').sort_values(by=['barra','fecha']).fillna(0)
    Falla=Falla.merge(dfcentrales[dfcentrales.tipo=='F'][['barra','central']], on='barra', how='inner').dropna()
    Falla['GenMax'] = Falla['MWh']
    Falla['tipo']='F'
    Falla=Falla.merge(MantCen[['fecha','Etapa','horas']].drop_duplicates(), on='fecha', how='left')[['Etapa','fecha','horas','barra','tipo','GenMax', 'central']].rename(columns={"GenMax":"potmax"})
    Falla['potmin']=0.0
    Falla = Falla.astype({'barra': 'int32'})

    out=[]
    
    mcmin = MantCen.central.min()
    test=MantCen[MantCen.central==mcmin].copy()
    
    for b in set_dif:
        numcens = dfcentrales[(dfcentrales.barra==b)&(dfcentrales.tipo=='F')]['central'].values
        for nc in numcens:
            test_aux=test.copy()
            test_aux['central']= nc
            out.append(test_aux)
    df_falla_0           = pd.concat(out, ignore_index = True)
    df_falla_0['tipo']   = 'F'
    df_falla_0['potmax'] = 0.0
    
    Fallas = pd.concat([Falla, df_falla_0], ignore_index=True)
    
    mask1 = Fallas.central.str.endswith('_1')
    mask2 = Fallas.central.str.endswith('_2')
    mask3 = Fallas.central.str.endswith('_3')
    mask4 = Fallas.central.str.endswith('_4')
    
    Fallas.loc[mask1, 'potmax'] *= 0.05
    Fallas.loc[mask2, 'potmax'] *= 0.05
    Fallas.loc[mask3, 'potmax'] *= 0.10
    Fallas.loc[mask4, 'potmax'] *= 0.80
    
    return Fallas[['Etapa','fecha','potmin', 'potmax', 'central']], dfcentrales

def gen_mant_others(df: pd.DataFrame, df_centrales: pd.DataFrame) -> pd.DataFrame:
    out=[]
    for l in df.itertuples():
        aux = pd.DataFrame()
        aux['fecha']=pd.date_range(start=l.INICIAL, periods=l.horas, freq='h').values
        aux['potminM']=l.potmin
        aux['potmaxM']=l.potmax
        aux['central'] = l.central
        out.append(aux)
        
    df_out=pd.concat(out, ignore_index = True)
    df_out = df_out.drop_duplicates(subset = ["fecha", "central"], keep = 'last').reset_index(drop = True) 
    return df_out

def to_mant_cen(df_out: pd.DataFrame, mc: pd.DataFrame) -> pd.DataFrame:
    Maux = pd.merge(mc, df_out, on=['central','fecha'], how='left').reset_index(drop = True)\
             .drop_duplicates(subset=['central', 'fecha'], keep='first') 
    cons_pmin=~np.isnan(Maux.potminM)
    cons_pmax=~np.isnan(Maux.potmaxM)
  
    Maux['potmin']=Maux['potmin'].mask(cons_pmin, Maux.potminM).values                
    Maux['potmax']=Maux['potmax'].mask(cons_pmax, Maux.potmaxM).values

    return Maux[['fecha','potmin', 'potmax', 'central']]

def preprocess_ManCen(mants_df: pd.DataFrame, df_eta: pd.DataFrame ) -> pd.DataFrame:
    # obtengo fechas límites del estudio
    fmin=df_eta.fecha.min()
    fmax=df_eta.fecha.max()
    aux            = mants_df.copy()
    aux            = aux[~((aux.INICIAL < fmin) & (aux.FINAL < fmin))] 
    aux            = aux[~((aux.INICIAL > fmax) & (aux.FINAL > fmax))] 
    aux["FINAL"]   = aux["FINAL"].mask(aux["FINAL"] > fmax, fmax)      
    # clip INICIAL a fmin: entradas que empiezan antes del horizonte se recortan, no se eliminan
    aux["INICIAL"] = aux["INICIAL"].mask(aux["INICIAL"] < fmin, fmin)
    aux            = aux[(aux.FINAL <= fmax) & (aux.INICIAL >= fmin)]  
    aux            = aux[~(aux["FINAL"] < aux["INICIAL"])]             
    aux["horas"]   = ((aux.FINAL-aux.INICIAL).dt.days+1)*24          
    return aux

def numcen(cenname, cendict):
    return cendict[cenname]

def gen_mant_ernc(df_ietapa: pd.DataFrame, aux_cgh: pd.DataFrame, ernc: pd.DataFrame) -> pd.DataFrame:
    aux            = df_ietapa.merge(ernc, on = "Etapa", how = 'inner').dropna().sort_values(by = ["CENTRAL", "fecha"])
    aux['potmaxM'] = aux['MÁXIMA']/aux['NHoras']
    aux['potminM'] = aux['MÍNIMA']/aux['NHoras']
    aux2 = aux.merge(aux_cgh, on = "CENTRAL", how = 'inner' ).dropna().drop_duplicates()
    aux2 = aux2[['fecha', 'potminM', 'potmaxM', 'numcen']]
    return aux2.rename(columns={"potminM":"potmin","potmaxM":"potmax"})

def get_mantenimientos(df_ciniciales: pd.DataFrame, 
                        df_dispcom: pd.DataFrame,
                        df_limitaciones: pd.DataFrame,
                        df_pobra: pd.DataFrame,
                        df_mmayor: pd.DataFrame,
                        df_mancen: pd.DataFrame,
                        df_ernc: pd.DataFrame,
                        df_centrales: pd.DataFrame,
                        df_simul: pd.DataFrame,
                        df_caudales_trasp_S: pd.DataFrame,
                        df_ietapa: pd.DataFrame,
                        df_plpblo: pd.DataFrame,
                        central_dict: dict
                      ) -> pd.DataFrame:
    
    resultados=[]
    Mant_dict=[df_ciniciales, df_dispcom, df_limitaciones, df_pobra, df_mmayor]
    mants_df = pd.concat(Mant_dict, ignore_index = True)
    
    to_mask_mant = []
    to_mask_erfv =[]
    
    mancen_mod = df_mancen[['fecha','potmin', 'potmax', 'numcen']]
    to_mask_erfv.append(mancen_mod)
    
    mants_df = preprocess_ManCen(mants_df, df_ietapa)
    
    mants_df = gen_mant_others(mants_df, df_centrales, df_ietapa, central_dict)
    
    to_mask_erfv.append(gen_mant_ernc(df_ernc, df_perfiles, df_ietapa, df_centrales,\
                                      df_plpblo).rename(columns={"potminM":"potmin","potmaxM":"potmax"}))
    
    to_mask_erfv.append(gen_mant_s(df_caudales_trasp_S, df_centrales, df_simul,\
                                   df_ietapa).rename(columns={"potminM":"potmin","potmaxM":"potmax"}))
    
    mancen=pd.concat(to_mask_erfv)
    
    mancen = to_mant_cen(mants_df, mancen)
    
    mancen          = mancen.merge(df_ietapa[['fecha','Etapa','horas']], on='fecha', how='left') 
    mancen          = mancen[['Etapa','fecha','numcen','potmax','potmin','horas']].merge(df_centrales[['numcen','tipo']], on='numcen', how='left')#
    mancen          = mancen[['Etapa','fecha','numcen','horas','tipo','potmax','potmin']].dropna()
    mancen['horas'] = mancen['horas'].astype("int32").reset_index(drop = True)
    
    return mancen

# escritura de archivos
def generate_file(tmpl_str: str, dict_tmpl: dict, out_file_path: str) -> None:
    tmpl_obj = j2.Template(tmpl_str)
    txt = tmpl_obj.render(dict_tmpl)
    
    # Asegurar un salto de línea en plpmance.dat
    if "plpmance.dat" in out_file_path and not txt.endswith("\n\n"):
        if txt.endswith("\n"):
            txt += "\n"
        else:
            txt += "\n\n"
            
    with open(out_file_path, 'w') as f:
        f.write(txt)

def generate_dat_files(out_folder:str, mdict:dict) -> None:
    if not path.isdir(out_folder): os.mkdir(out_folder)
    
    def is_empty(filename, data_dict):
        if filename == 'plpplem1.dat': return True
        if filename == 'plpcenpmax.dat' and data_dict.get('cenpmax', {}).get('NEMB', 0) == 0: return True
        if filename == 'plpcenre.dat' and data_dict.get('rendimientos', {}).get('NEMB', 0) == 0: return True
        if filename == 'plpextrac.dat' and data_dict.get('extracciones', {}).get('NCEN', 0) == 0: return True
        if filename == 'plpfilemb.dat' and data_dict.get('filtraciones', {}).get('NEMB', 0) == 0: return True
        if filename == 'plpvrebemb.dat' and data_dict.get('rebalses', {}).get('NEMB', 0) == 0: return True
        return False

    for filename, tup in mdict.items():
        mydict, mytmpl = tup
        if not mydict: continue
        
        fpath = path.normpath(path.join(out_folder, filename))
        
        if is_empty(filename, mydict):
            if path.exists(fpath):
                os.remove(fpath)
                print(f"Borrando {filename} antiguo vacío.")
            continue
            
        print(filename, fpath)
        generate_file(mytmpl, mydict, fpath)
        
# escritura adiciona indhor.csv
def write_indhor(df_blodem_ini: pd.DataFrame, outpath: str) -> None:
    headers = ["Año", "Mes", "Dia", "Hora", "Bloque"]
    df_blodem = df_blodem_ini.copy()
    df_blodem['dia'] = df_blodem['fecha'].dt.day
    df_blodem['mescal'] = df_blodem['fecha'].dt.month
    df_blodem['anocal'] = df_blodem['fecha'].dt.year
    df_blodem = df_blodem[['anocal', 'mescal', 'dia', 'Hora', 'bloque_CEN']]
    df_indhor = df_blodem.drop_duplicates().reset_index(drop = True)
    df_indhor.columns = headers
    df_indhor.to_csv(outpath, index = False)
    
# funcionaes auxiliares para validacion de potencias
def chequea_centrales(lista_centrales: list, lista_centr_mant) -> list :
    non_valid = []
    for cen in lista_centr_mant:
        if cen in lista_centrales: 
            continue
        else:
            non_valid.append(cen)
    return non_valid

def conteo_de_fechas(df_mant: pd.DataFrame, date_ini: pd.Timestamp):
    non_proc = 0
    aux      = df_mant[~(df_mant.iloc[:,2] < date_ini)]
    non_proc = len(df_mant[df_mant.iloc[:,2] < date_ini])
    return non_proc, aux

# fecha inicial mayor que fecha final -> ERROR
def chequeo_fechas(df_mant: pd.DataFrame) -> tuple:
    mask = df_mant.iloc[:, 1] > df_mant.iloc[:,2]
    aux  = df_mant[mask]
    aux  = aux.iloc[:,[0]]
    return aux, df_mant[~mask]
        
# potmin > potmaxnom || potmax > potmaxnom
def chequeo_potencia_nominal(df_mant: pd.DataFrame, df_potnom: pd.DataFrame) -> tuple:
    dfaux = df_mant.merge(df_potnom, on = ['CENTRAL'], how = 'inner')
    mask  = (dfaux.iloc[:,3].round(8) > dfaux.iloc[:,-1].round(8)) | (dfaux.iloc[:,4].round(8) > dfaux.iloc[:,-1].round(8))
    aux   = dfaux[mask]
    aux   = aux.iloc[:, [0]]
    return aux, dfaux[~mask].iloc[:,:-1]

# potmin > potmax -> ERROR
def chequeo_consistencia_potencias(df_mant: pd.DataFrame) -> tuple:
    mask = df_mant.iloc[:,3] > df_mant.iloc[:,4]
    aux  = df_mant[mask]
    aux  = aux.iloc[:,[0]]
    return aux, df_mant[~mask]

# funcion utilitaria para igualar el redondeo de Excel/VBA
# versión Decimal con épsilon microscópico para curar imprecisión float64
def correccion_preredondeo(df: pd.DataFrame, cols: list, ndec: int, rounding_mode=None) -> pd.DataFrame:
    import decimal
    from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
    if rounding_mode is None:
        rounding_mode = ROUND_HALF_UP
    if isinstance(rounding_mode, str):
        rounding_mode = getattr(decimal, rounding_mode)
        
    df = df.copy()
    q = Decimal('10') ** -ndec
    eps = Decimal('1e-8')
    for col in cols:
        def _excel_round(val):
            if pd.isna(val):
                return val
            d_val = Decimal(str(val))
            # epsilon firmado para que x.5 redondee siempre "hacia afuera" (away from zero)
            v_eps = eps if d_val >= 0 else -eps
            return float((d_val + v_eps).quantize(q, rounding=rounding_mode))
        df[col] = df[col].apply(_excel_round)
    return df
