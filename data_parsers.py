import pandas as pd
import numpy as np
import datetime
import calendar

from scipy.stats import norm
from sklearn.cluster import KMeans, AgglomerativeClustering

from contenedores_auxiliares import CHG_COL_NAME, NAMES_DICT_CEN
from func_cdec import Embalses
from utils import *
########## Funciones que operan los dataframes de entrada (y algunas auxiliares)


######### ETA y BLO
mes_dict = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 
            'May': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}

def mes_a_imes(x):
    return mes_dict[x]

def get_tasa(x):
    global prev
    if x.name == 0:
        prev = 1.0
        return 1.0
    elif x.mes != x.mes1:
        prev = prev * (1.1)**(1/12)
        return prev
    else:
        return prev

######### ETAPAS
# modificado jul 2025 -> compatibilidad json
def parse_etapas(df_etapas_xls: pd.DataFrame) -> pd.DataFrame:
    #df_eta = df_etapas_xls.reset_index(drop = True)
    df_eta = df_etapas_xls.copy()
    df_eta = df_eta.dropna(subset=['Etapa', 'Nº Bloques'])
    df_eta = df_eta.astype({'Etapa': 'int32', 'Nº Días': 'int32', 'Año': 'int32', 'Nº Bloques': 'int32' })
    df_eta['Inicial'] = pd.to_datetime(df_eta['Inicial'])
    df_eta['Final'] = pd.to_datetime(df_eta['Final'])
    df_eta["NHoras"] = 24*df_eta['Nº Días']
    
    IniMes=df_eta.Inicial.dt.month.iloc[0].astype("int16")
    
    i=0
    for t in df_eta.Inicial.dt.month:
        if t==IniMes:
            i+=1
        else:
            break
    IniSem=4*IniMes-i-1
    
    etapas_full=pd.DataFrame()
    
    etapas_full["Etapa"] = np.arange(1, len(df_eta) +1)
    etapas_full["NHoras"] = df_eta["NHoras"]
    etapas_full["NDias"] = df_eta["Nº Días"]
    etapas_full["Inicial"] = df_eta["Inicial"]
    
    #print(etapas_full, df_eta["Inicial"])
    dias=['LU','TR','TR','TR','TR','SA','DO']
    
    
    
    etapas_full['mes']     = etapas_full['Inicial'].dt.month
    etapas_full['Semana']  = etapas_full['Etapa'].apply(lambda x: (IniSem + x+1) % 48 if (IniSem + x+1) != 48 else 48)
    etapas_full['dia']     = etapas_full['Inicial'].dt.day
    etapas_full['diaw']    = etapas_full['Inicial'].dt.day_of_week
    etapas_full['diay']    = etapas_full['Inicial'].dt.day_of_year
    etapas_full['HORA']    = etapas_full['Inicial'].dt.hour+1
    etapas_full['Año']     = etapas_full['Inicial'].dt.year
    etapas_full['horas']   = 24*(etapas_full['diay']-1) + etapas_full['HORA']
    
    etapas_full["Año"] = etapas_full["Año"] - etapas_full["Año"].min() + 1
    etapas_full["FDesh"] = 'F'
    mask = (etapas_full.index <=1) | ((etapas_full.mes >= 4) & (etapas_full.mes <= 9))
    if not etapas_full[~mask].empty:
        etapas_full.loc[~mask, "FDesh"] = 'T'
    
    
    etapas_full = etapas_full.reset_index()
    etapas_full["mes1"] = etapas_full["mes"].shift(1).astype('int32', errors = 'ignore') # necesarrio para facttasa
    etapas_full["FactTasa"] = etapas_full.apply(get_tasa, axis = 1)
    etapas_full["TipoEtapa"] = df_eta["Nº Bloques"].astype(str) + " Bloques"
    
    # año y mes hidrológico
    etapas_full["AñoHid"] = 1
    etapas_full["MesHid"] = (etapas_full["mes"] - 3)% 12
    etapas_full.loc[etapas_full["MesHid"] == 0, "MesHid"] = 12
    
    etapas_full["mes"] = etapas_full["MesHid"]
    
    aprev = 1
    etapas_full["AñoHid"] = 1
    for irow, row in etapas_full.iterrows():
        if irow == 0: continue
        ahid = row["mes"]
        ahid_prev = etapas_full.loc[irow - 1, "mes"]
        if ahid == 1 and ahid_prev != 1:
            aprev += 1
        etapas_full.loc[irow, "AñoHid"] = aprev

    etapas_full["Año"] = etapas_full["AñoHid"]
    
    return etapas_full[["Año", "mes", "Etapa", "FDesh", "NHoras", "FactTasa", "TipoEtapa"]].copy()

def parse_bloques(df_blodem: pd.DataFrame) -> pd.DataFrame:
    df_blo = df_blodem[['Etapa','Mes','bloque_CEN', 'indblo', 'horas_CEN', 'fecha', 'Año']].copy()
    #df_blo['Ano'] = df_blo['fecha'].dt.year
    #df_blo['Ano'] = df_blo['Ano'] - df_blo['Ano'].min() + 1
    df_blo = df_blo.drop('fecha', axis = 1)
    df_blo = df_blo.drop_duplicates().reset_index(drop = True)
    df_blo['indice'] = df_blo.index + 1
    df_blo["tipo"] = df_blo["indblo"].apply(lambda x: f"Bloque {x:02d}")
    df_blo = df_blo.drop('indblo', axis = 1)
    df_blo['horas_CEN'] = df_blo['horas_CEN'].astype('int32')
    df_blo = df_blo.rename(columns = {'Año': 'Ano'})
    
    return df_blo[['indice', 'Etapa', 'horas_CEN', 'Ano', 'Mes', 'tipo']]


######### BARRAS
# solo para estructura
def parse_barras(df_barras_xls: pd.DataFrame) -> pd.DataFrame:
    df_bar = df_barras_xls.dropna(how = 'all').dropna(how = 'any')
    return df_bar

######### LINEAS
def parse_lineas(df_lineas_xls: pd.DataFrame) -> pd.DataFrame:
    df_lineas = df_lineas_xls.copy()
    df_lineas = df_lineas.dropna(how = 'any')
    df_lineas["Operativa"] = df_lineas["Operativa"].apply(lambda x: 'T' if x else 'F')
    df_lineas["Pérdidas"]  = df_lineas["Pérdidas"].apply(lambda x: 'T' if x else 'F')
    df_lineas = df_lineas[["Nombre A->B","A->B","B->A","Barra A","Barra B", "V [kV]","R[ohm]","X[ohm]","Pérdidas","Nº de Tramos","Operativa"]]
    return df_lineas

######### EXTRACCIONES
# solo para estructura
def parse_extracciones(df_extracciones_xls: pd.DataFrame) -> pd.DataFrame:
    return df_extracciones_xls

######### RENDIMIENTOS
# solo para estructura
def parse_rendimientos(df_rendimientos_xls: pd.DataFrame, df_centrales_xls) -> pd.DataFrame:
    df_cen = df_centrales_xls.copy()
    df_cen = df_cen.rename(columns=CHG_COL_NAME)
    df_rend = df_rendimientos_xls.merge(df_cen[['central','numcen','rendimiento']], on='central', how='left')
    return df_rend

######### FILTRACIONES

def parse_filtraciones(df_filtraciones_xls: pd.DataFrame, df_centrales_xls) -> tuple:
    df_cen = df_centrales_xls.copy()
    df_cen = df_cen.rename(columns=CHG_COL_NAME)
    central_dict  = {x[1]:x[0] for x in df_cen[(df_cen.tipo !='X')][['numcen','central']].values}
    df_filtraciones_xls["numcen"] = df_filtraciones_xls["central"].apply(lambda x: central_dict[x])
    df_filtraciones_xls["numcenFin"] = df_filtraciones_xls["centralFin"].apply(lambda x: central_dict[x])
    df_filtraciones_xls['const_mod']=df_filtraciones_xls['const']-df_filtraciones_xls['pend']*df_filtraciones_xls['vol']
    df_aux = df_filtraciones_xls.groupby("central").agg({'centralFin':'first','filtrmedia':'first', 'ntramos': 'first', 'numcen': 'first', 'numcenFin': 'first'}).reset_index()
    df_aux2 = df_filtraciones_xls[['central', 'tramo','vol', 'pend', 'const', 'const_mod']].set_index(["central"])
    embnames = df_aux2.index.tolist()
    return df_aux, df_aux2, embnames

######### REBALSES
# solo para estructura
def parse_rebalses(df_rebalses_xls: pd.DataFrame) -> pd.DataFrame:
    return df_rebalses_xls[['central', 'volreb', 'costo']]

######### BATERIAS
def parse_baterias(df_bat_xls: pd.DataFrame) -> pd.DataFrame:
    df = df_bat_xls.copy()
    df = df.dropna(subset=['INDICE'])
    df = df[pd.to_numeric(df['INDICE'], errors='coerce').notna()].copy()
    df['INDICE']                  = df['INDICE'].astype(int)
    df['Conectada a la Barra']    = df['Conectada a la Barra'].astype(int)
    df['Rendimiento de Descarga'] = pd.to_numeric(df['Rendimiento de Descarga'], errors='coerce').fillna(0.0)
    df['Mínima']                  = pd.to_numeric(df['Mínima'], errors='coerce').fillna(0.0)
    df['Máxima']                  = pd.to_numeric(df['Máxima'], errors='coerce').fillna(0.0)
    df['Central de Carga']        = df['Central de Carga'].astype(str).str.strip()
    df['Rendimiento de Carga']    = pd.to_numeric(df['Rendimiento de Carga'], errors='coerce').fillna(0.0)
    return df.reset_index(drop=True)

######### CENPMAX
def parse_cenpmax(df_cenpmax_xls: pd.DataFrame) -> tuple:
    df_aux = df_cenpmax_xls.groupby("central").agg({'embalse':'first', 'ntramos': 'first'}).reset_index()
    df_aux2 = df_cenpmax_xls[['central','vol', 'pend', 'const']].set_index(["central"])
    embnames = df_aux2.index.unique().tolist()
    return df_aux, df_aux2, embnames

######### LAJA
# solo para estructura
def parse_laja(df_laja_xls: pd.DataFrame) -> pd.DataFrame:
    df_laja = df_laja_xls.dropna(how = 'all').dropna(subset = "RESTRICCIÓN")
    return df_laja

######### MAULE
def parse_maule(df_maule_xls: pd.DataFrame) -> pd.DataFrame:
    df_maule = df_maule_xls.dropna(how = 'all').dropna(subset = "RESTRICCIÓN")
    return df_maule

######## CENTRALES
def parse_centrales(df_centrales_xls: pd.DataFrame, uninodal = False) -> tuple:
    df_cgh = df_centrales_xls.copy()
    df_cgh = df_cgh.rename(columns=CHG_COL_NAME)
    df_cgh['barra'] = df_cgh['barra'].fillna(0).astype("int32")
    df_cgh = df_cgh[~np.isnan(df_cgh.numcen)].reset_index(drop=True)
    df_cgh['numcen'] = df_cgh['numcen'].astype("int16")
    df_cgh['cvariable'] = df_cgh['cvariable'].replace(np.nan, 0.0)
    df_cgh['cvariable'] = df_cgh['cvariable'].astype(float).replace(np.nan, 0.0)
    df_cgh['afl1ersem'] = df_cgh['afl1ersem'].astype(float).replace(np.nan, 0.0)
    df_cgh['potmin'] = df_cgh['potmin'].astype(float).replace(np.nan, 0.0)
    df_cgh['potmax'] = df_cgh['potmax'].astype(float).replace(np.nan, 0.0)
    df_cgh['indhid'] = df_cgh['indhid'].replace(np.nan, 'F').replace(1.0, 'T')
    df_cgh['ggen'] = df_cgh['ggen'].replace(np.nan, 0.0).astype('int32')
    df_cgh['gvert'] = df_cgh['gvert'].replace(np.nan, 0.0).astype('int32')
    #mask = df_cgh['fcf'].isnull()
    #df_cgh['fcf'] = df_cgh['fcf'].astype("str", errors = 'ignore') 
    #df_cgh.loc[mask, 'fcf'] = 'F'
    
    df_cgh['fcf'] = df_cgh['fcf'].replace(0.0, 'F').replace(np.nan, 'F' ).replace(1.0, 'T')
    
    if uninodal:
        df_cgh.loc[df_cgh.barra > 1, 'barra'] = 1

    embalses = df_cgh[df_cgh.tipo == 'E']
    series   = df_cgh[df_cgh.tipo.isin(['S', 'R'])]
    pasadas  = df_cgh[df_cgh.tipo.isin(['P', 'M'])]
    baterias = df_cgh[df_cgh.tipo == 'BAT']
    termicas = df_cgh[df_cgh.tipo == 'T']
    fallas   = df_cgh[df_cgh.tipo == 'F']
    
    ncen = len(embalses)+len(series)+len(pasadas)+len(termicas)+len(baterias)+len(fallas)
    
    # CORRECCIÓN Y RED DE SEGURIDAD: Llenar nulos de volumen calculando desde la tabla cota-volumen si existe, si no, llenar con 0
    from func_cdec import Embalses
    emb_calc = Embalses()
    
    def interpolate_vol(row, vol_col, cota_col):
        vol = row[vol_col]
        if pd.isna(vol):
            try:
                cota = row[cota_col]
                central_name = str(row['central']).strip().lower()
                if pd.notna(cota):
                    calc_vol = emb_calc.volumen(central_name, float(cota))
                    if calc_vol is not None:
                        return calc_vol
            except Exception:
                pass
            return 0.0
        return vol

    def interpolate_rend(row, rend_col, cota_col):
        rend = row[rend_col]
        if pd.isna(rend):
            try:
                cota = row[cota_col]
                central_name = str(row['central']).strip().lower()
                if pd.notna(cota):
                    calc_rend = emb_calc.rendimiento(central_name, float(cota))
                    if calc_rend is not None:
                        return calc_rend
            except Exception:
                pass
            return 0.0
        return rend

    embalses = embalses.copy()
    embalses['rendimiento'] = embalses.apply(lambda r: interpolate_rend(r, 'rendimiento', 'cotainicial'), axis=1)
    embalses['volini'] = embalses.apply(lambda r: interpolate_vol(r, 'volini', 'cotainicial'), axis=1)
    embalses['volfin'] = embalses.apply(lambda r: interpolate_vol(r, 'volfin', 'cotafinal'), axis=1)
    embalses['volmin'] = embalses.apply(lambda r: interpolate_vol(r, 'volmin', 'cotamin'), axis=1)
    embalses['volmax'] = embalses.apply(lambda r: interpolate_vol(r, 'volmax', 'cotamax'), axis=1)

    # preproceso dataframe de embalses
    embalses = embalses.iloc[:,[0,1,3,4,5,6,7,8,11,12,22,23,24,25,26,27,28,29]].copy()
    
    # Llenar nulos sobrantes con 0
    embalses[['volini','volfin', 'volmin', 'volmax' ]] = embalses[['volini','volfin', 'volmin', 'volmax' ]].fillna(0.0)
    embalses[['volini','volfin', 'volmin', 'volmax' ]] = embalses[['volini','volfin', 'volmin', 'volmax' ]] * 1e6 
    
    # corregido may2025 - Seguro contra valores NaN o 0 en el cálculo del logaritmo
    vol_max_safe = embalses['volmax'].clip(lower=1.0)
    embalses['FEsc'] = vol_max_safe.apply(lambda x: 10**(int(np.log10(x) + 0.5))).astype('int64')
    embalses[['volini','volfin', 'volmin', 'volmax' ]] = embalses[['volini','volfin', 'volmin', 'volmax' ]].div(embalses['FEsc'], axis = 0)
    
    # preproceso de los que restan
    series   = series.iloc[:,[0,1,3,4,5,6,7,8,11,12,26,27,28,29]].copy()
    pasadas  = pasadas.iloc[:,[0,1,3,4,5,6,7,8,11,12,26,27,28,29]].copy()
    termicas = termicas.iloc[:,[0,1,3,4,5,6,7,8,11,12,26,27,28,29]].copy()
    baterias = baterias.iloc[:,[0,1,3,4,5,6,7,8,11,12,26,27,28,29]].copy()
    fallas   = fallas.iloc[:,[0,1,3,4,5,6,7,8,11,12,26,27,28,29]].copy()
    
    return embalses, series, pasadas, termicas, fallas, baterias, ncen

######## AFLUENTES
# modificado jul2025, ago2025 -> compatibilidad json, formato salida
def parse_afluentes(df_hid_xls: pd.DataFrame, # hoja hidrologia
                    df_ah1_xls: pd.DataFrame, # hoja caudales ah1
                    df_ah2_xls: pd.DataFrame, # hoja caudales ah2
                    df_his_xls: pd.DataFrame, # hoja historicos
                    df_eta_xls: pd.DataFrame, # hoja etapas
                    df_cen_xls: pd.DataFrame, # hoja centrales
                    df_fla_xls: pd.DataFrame, # hoja datos flags especificos
                    sim_type  : TipoSimulacion, # 'flag' de tipo de simulacion
                   ) -> tuple:
    
    
    df_hid = df_hid_xls.copy()
    df_hid = df_hid.drop("Unnamed: 2", axis = 1)
    df_hid.rename(columns = {"Unnamed: 1": "dato", "Unnamed: 3": "valor"}, inplace = True)
    df_hid = df_hid.set_index("dato", drop = True)

    df_ah1 = df_ah1_xls.copy()
    df_ah1 = df_ah1.dropna(subset = "CENTRAL")
    #print(df_ah1)
    df_ah2 = df_ah2_xls.copy()
    df_ah2 = df_ah2.dropna(subset = "CENTRAL")
    #print(df_ah2)
    df_his = df_his_xls.copy()
    df_his = df_his.dropna(subset = "CENTRAL")
    df_eta = df_eta_xls.copy()
    df_eta = df_eta.dropna(subset=['Etapa', 'Nº Bloques'])
    df_eta = df_eta.astype({'Etapa': 'int32', 'Nº Días': 'int32', 'Año': 'int32', 'Nº Bloques': 'int32' })
    
    df_eta["Inicial"] = pd.to_datetime(df_eta["Inicial"])
    df_eta["Final"] = pd.to_datetime(df_eta["Final"])

    df_cen = df_cen_xls.copy()
    df_fla = df_fla_xls.dropna().set_index(df_fla_xls.columns[0], drop = True).astype(bool)
    
    NHidro    = df_hid.loc["Número de Hidrologías", "valor"]
    NCau      = int( len(df_ah1) / NHidro )
    NombreCau = list(df_ah1.CENTRAL.unique())
    MesIniCal = df_eta.loc[0,"Inicial"].month
    NSemCDEC  = 48
    NDiaS     = [ 7, 8, 7, 8, #ABR
                  7, 8, 8, 8, #MAY
                  7, 8, 7, 8, #JUN
                  7, 8, 8, 8, #JUL
                  7, 8, 8, 8, #AGO
                  7, 8, 7, 8, #SEP
                  7, 8, 8, 8, #OCT
                  7, 8, 7, 8, #NOV
                  7, 8, 8, 8, #DIC
                  7, 8, 8, 8, #ENE
                  7, 7, 7, 7, #FEB
                  7, 8, 8, 8] #MAR

    NFil       = len(df_eta)
    NEta       = int(df_eta["Nº Bloques"].sum()) # se mantiene el nombre de la variable de la macro
    NEta_Alf4s = 4
    MesIni     = MesIniCal
    MesEtaCal  = df_eta.loc[0:(NEta_Alf4s - 1), "Inicial"].dt.month
    bisiesto   = calendar.isleap(df_eta.loc[0,"Inicial"].year)
    NCenEst    = int(df_cen["Afluente Estocástico"].sum())
    NCen       = len(df_cen)
    NCen_Pro   = int(df_cen["Pronóstico de Deshielo"].sum()) if MesIni > 7 or MesIni < 4 else -1
    MesIni     = df_eta.loc[0,"Inicial"].month
    FlPdD      = df_fla.loc["Flag Pronóstico Deshielo"].iloc[0] # flag de pronostico de deshielo celda 'Datos'
    NEta4SubP  = df_eta.loc[:(NEta_Alf4s - 1), "Nº Bloques"].sum()    

    # ajuste a indexación año cdec ¿?

    if MesIniCal > 3:
        MesIniC = MesIniCal - 3
    else:
        MesIniC = MesIniCal + 9

    SemAux = (MesIniC - 1)*4
    
    ## Codigo asociado a rutina AFLU4S_DH
    
    dict_ah1 = afluentes_ah_a_diccionario(df_ah1)
    dict_ah2 = afluentes_ah_a_diccionario(df_ah2)
    dict_his = afluentes_ah_a_diccionario(df_his)
    
    # rellena caudales semanales segun particion dada por SemAux
    dict_qsem = {}
    for afl_name in dict_ah1.keys():
        df_ah1_cen = dict_ah1[afl_name]
        df_ah2_cen = dict_ah2[afl_name]
        aux2 = df_ah2_cen.iloc[:, 1:(SemAux + 1)]
        aux1 = df_ah1_cen.iloc[:,(SemAux + 1):(NSemCDEC + 1)]
        dict_qsem[afl_name] = pd.concat([aux2, aux1], axis = 1)

    # rellena caudales diarios a aprtir de caudales semanales
    dict_qdia = {}
    NDANO = 365
    cols = []
    nd = 0
    for k,nds in enumerate(NDiaS):
        for j in range(1, nds+1):
            nd += 1
            cname = "d"+str(nd)
            cols.append(cname)


    aux = pd.DataFrame(0.0, index=np.arange(NHidro), columns = cols) 


    for afl_name in dict_ah1.keys():
        df_qsem = dict_qsem[afl_name]
        a = aux.copy()
        offset = 0
        # enero a marzo
        for isem, nds in enumerate(NDiaS[36:]):
            vals = np.repeat(df_qsem.iloc[:,(36+isem)].values, nds).reshape(NHidro,nds)
            a.iloc[:,(offset):(offset+nds)] = vals
            offset += nds
        # abril a diciembre
        for isem, nds in enumerate(NDiaS[:36]):
            vals = np.repeat(df_qsem.iloc[:,isem].values, nds).reshape(NHidro,nds)
            a.iloc[:,(offset):(offset+nds)] = vals
            offset += nds

        #for isem, nds in enumerate
        dict_qdia[afl_name] = a.copy()
        
    
    # arreglo agno bisiesto

    dict_qdiabis = {}
    NDiaSbis = list(NDiaS)
    NDiaSbis[43] = 8

    colsb = cols + ["d366"]
    aux = pd.DataFrame(0.0, index=np.arange(NHidro), columns = colsb)

    for afl_name, df_qdia in dict_qdia.items():
        a = aux.copy()
        a.iloc[:,:59] = df_qdia.iloc[:,:59]  # esto queda igual
        a.iloc[:,59:60] = a.iloc[:,58:59]    # dia adicional en febrero
        a.iloc[:,60:] = df_qdia.iloc[:,59:]

        dict_qdiabis[afl_name] = a.copy()
        
    # llenaado de caudales etapa 4s inicial
    dict_qeta = {}
    aux = pd.DataFrame(0.0,index = np.arange(NHidro), columns = [str(i) for i in np.arange(1,NEta_Alf4s+1)])

    for afl_name, df_qdia in dict_qdia.items():
        df_qdiabis = dict_qdiabis[afl_name]
        a = aux.copy()
        for ieta in range(NEta_Alf4s):

            fini = df_eta.loc[ieta,"Inicial"]
            ffin = df_eta.loc[ieta,"Final"]
            FechaI = (fini - datetime.datetime(fini.year - 1, 12, 31)).days
            FechaF = (ffin - datetime.datetime(ffin.year - 1, 12, 31)).days
            bisiesto = calendar.isleap(fini.year)
            #print("ieta: ", ieta, " FechaI: ", FechaI, " FechaF", FechaF, " bis: ", bisiesto)
            if bisiesto:
                df_qd = df_qdiabis
                ndias = 366
            else:
                df_qd = df_qdia
                ndias = 365

            qmed = np.zeros(NHidro)
            for idia in range(FechaI, FechaF + 1):

                idia_a = idia
                if idia > ndias: idia_a -= ndias
                col = "d" + str(int(idia_a))
                #print("\t", col, " valor", df_qd.loc[0,col])
                qmed += df_qd.loc[:,col]

            qmed = qmed / (FechaF-FechaI+1)

            a.iloc[:,ieta] = qmed
        dict_qeta[afl_name] = a.copy()

    # estadisticas
    aux = pd.DataFrame(0.0, index = dict_qeta.keys(), columns = [str(i) for i in np.arange(1,NEta_Alf4s +1)])

    dict_qeta_pro = {}
    dict_qeta_des = {}
    dict_qeta_min = {}
    dict_qeta_max = {}

    for afl_name, df_qeta in dict_qeta.items():
        df_qeta = df_qeta.astype("float32")
        ln_qeta = np.log(np.maximum(df_qeta, 0.01))
        dict_qeta_min[afl_name] = df_qeta.min(axis = 0)
        dict_qeta_max[afl_name] = df_qeta.max(axis = 0)


        dict_qeta_pro[afl_name] = ln_qeta.mean(axis = 0)
        dict_qeta_des[afl_name] = ln_qeta.std(axis = 0).replace(0.0,1.0)
        
    # calculo de la probabilidad de excedencia
    dict_pbb_exc = {}
    m = 1e8
    for afl_name, df_qeta in dict_qeta.items():
        df_qeta = df_qeta.astype("float32")
        medias  = dict_qeta_pro[afl_name]
        desv    = dict_qeta_des[afl_name]

        ln_qeta = np.log(np.maximum(df_qeta,0.01))
        normal  = norm.cdf(ln_qeta, loc = medias, scale = desv)
        dict_pbb_exc[afl_name] = pd.DataFrame(normal, index = range(NHidro), columns = [str(i) for i in range(1, NEta_Alf4s + 1)])
        
    # calculo de correlacion entre etapas
    dict_corr = {}

    for afl_name, df_qeta in dict_qeta.items():
        ln_eta_all     = np.log(np.maximum(df_qeta, 0.01))
        dict_corr[afl_name] = ln_eta_all.corr().iloc[0,1:].fillna(0.0)
        
    
    # pronostico de deshielo

    if MesIni > 7 or MesIni < 4:
        # aca se guardan los nombres de las centrales (Nom_Est_Pro), 
        # los volumnes maximos y minimos (VolMin, VolMax) 
        # la fecha del pronostico y el indice del mes de pronostico (MesPro)
        df_desh = df_cen[df_cen["Pronóstico de Deshielo"] == 1.0][["CENTRALES","Volumen Mínimo hm3", "Volumen Máximo hm3","Mes del Pronóstico"]].copy()
        df_desh["Mes del Pronóstico"] = pd.to_datetime(df_desh["Mes del Pronóstico"])
        df_desh["imes"] = df_desh["Mes del Pronóstico"].dt.month
        df_desh[["Volumen Mínimo hm3", "Volumen Máximo hm3"]] = df_desh[["Volumen Mínimo hm3", "Volumen Máximo hm3"]].astype("float32") 

        dict_desh_ord_aux = {}
        # nombres del pronostico asociado 
        Nom_Est_ProAso = list(df_cen["Pronóstico Asociado"])

        df_vol_desh = pd.DataFrame(0.0, index = np.arange(NHidro), columns = df_desh["CENTRALES"].values)
        df_vol_desh = df_vol_desh.astype({col: 'float32' for col in df_vol_desh.columns})

        IndHid = pd.DataFrame(-1, index = np.arange(NHidro), columns = df_desh["CENTRALES"].values )

        for row in df_desh.iterrows():

            cname   = row[1]["CENTRALES"]
            mes_pro = row[1]["imes"]
            f_pro   = row[1]["Mes del Pronóstico"]
            vmax    = row[1]["Volumen Máximo hm3"]
            vmin    = row[1]["Volumen Mínimo hm3"]

            if mes_pro <= 3:
                FechaIDes = (datetime.datetime(f_pro.year, mes_pro, 1) - datetime.datetime(f_pro.year - 1, 12, 31)).days
                FechaFDes = (datetime.datetime(f_pro.year, 3, 31) - datetime.datetime(f_pro.year - 1, 12, 31)) .days
                bis1      = calendar.isleap(f_pro.year)
                bis2      = False
            else:
                FechaIDes = (datetime.datetime(f_pro.year, mes_pro, 1) - datetime.datetime(f_pro.year - 1, 12, 31)).days 
                FechaFDes = (datetime.datetime(f_pro.year + 1, 3, 31) - datetime.datetime(f_pro.year - 1, 12, 31)).days 
                bis1      = calendar.isleap(f_pro.year)
                bis2      = calendar.isleap(f_pro.year + 1)
                #print(FechaIDes, FechaFDes)

            #if cname == "HLH_AZUFRE_RN": print("CENTRAL: ", cname, " vmin: ",vmin, " vmax: ", vmax, " f_pro: ", f_pro, "mes_pro: ", mes_pro )
            #if cname == "HLH_AZUFRE_RN": print("FechaIDes: ", FechaIDes, " FechaFDes: ", FechaFDes, " bis1: ", bis1, " bis2: ", bis2)

            # se obtienen los caudales diarios 
            df_qdia    = dict_qdia[cname]
            df_qdia    = df_qdia.astype({col: 'float32' for col in df_qdia.columns})
            df_qdiabis = dict_qdiabis[cname]
            df_qdiabis = df_qdiabis.astype({col: 'float32' for col in df_qdiabis.columns})

            # hay que vectorizar esta ensalada que hay abajo
            for IHid in range(NHidro):
                VolAux = 0.0
                qdiah    = df_qdia.iloc[IHid,:]
                qdiahbis = df_qdiabis.iloc[IHid,:]
                for idia in range(FechaIDes, FechaFDes + 1):
                    if not bis1:
                        if idia > 365:
                            IDia_a = idia - 365
                        else:
                            IDia_a = idia
                        if bis2 and (idia > 365):
                            VolAux += qdiah.iloc[IDia_a - 1] * 0.0864
                        else:
                            VolAux += qdiahbis.iloc[IDia_a - 1] * 0.0864
                    else:
                        if idia > 366:
                            IDia_a = idia - 366
                        else:
                            IDia_a = idia

                        if (not bis2) and (idia > 366):
                            VolAux += qdiah.iloc[IDia_a - 1] * 0.0864
                        else:
                            VolAux += qdiahbis.iloc[IDia_a - 1] * 0.0864
                df_vol_desh.loc[IHid, cname] = np.float32(VolAux)
            dict_desh_ord_aux[cname] = df_vol_desh.loc[:, cname].sort_values(ascending = False)
            prob_exc_des = (2 * np.arange(1, NHidro + 1) - 1) / (2 * NHidro)

            aux = dict_desh_ord_aux[cname].reset_index(drop = True)

            #print("\n\ncentral:", cname, dict_desh_ord_aux[cname].iloc[-1] > vmax, vmax, dict_desh_ord_aux[cname].iloc[-1])
            if  dict_desh_ord_aux[cname].iloc[-1] > vmax:
                print("Error: Volumen Máximo período menor que mínimo estadística: ", cname)
            if  dict_desh_ord_aux[cname].iloc[0] < vmin:
                print("Error: Volumen Mínimo período mayor que máximo estadística: ", cname)
            if  vmax < vmin:
                print("Error: Volumen Mínimo período mayor que volumen máximo período: ", cname)

            j = aux[aux - vmax <= 0.0 ].index[0]
            hid_max = j
            if dict_desh_ord_aux[cname].iloc[-1] >= vmin:
                hid_min = NHidro - 1
                #print("\t hid_min = NHidro - 1")
            else:
                while (dict_desh_ord_aux[cname].iloc[j] >= vmin and j < NHidro):
                    j +=1   
                hid_min = j - 1

            #if cname == "HLH_AZUFRE_RN": print("\tord: ",dict_desh_ord_aux[cname])
            #if cname == "HLH_AZUFRE_RN": print("\thidmax: ", hid_max, " hidmin: ", hid_min)
            N_Est_Red = hid_min - hid_max + 1

            if (N_Est_Red <= 1):
                print("Error. Estadística reducida a sólo un año: ", cname, hid_min, hid_max)
                #print(aux, vmax, vmin)
            #if cname == "HLH_AZUFRE_RN": print("\tN_ESt_Red: ", N_Est_Red)

            prob_red   = np.zeros(N_Est_Red)
            ind_aux1 = np.zeros(N_Est_Red).astype(np.int32)
            for IRed in range(N_Est_Red):
                prob_red[IRed] = (IRed + 1) / N_Est_Red
                ind_aux1[IRed] = int(dict_desh_ord_aux[cname].index[hid_max + IRed])

            #if cname == "HLH_AZUFRE_RN": print("\tprobred: ",prob_red)
            #if cname == "HLH_AZUFRE_RN": print("\tind_aux1: ",ind_aux1)
            #if cname == "HLH_AZUFRE_RN": print("\tord[ind_aux1]: ",dict_desh_ord_aux[cname].loc[ind_aux1])
            j = 0
            ind_aux = dict_desh_ord_aux[cname].index
            #if cname == "HLH_AZUFRE_RN": print("\tind_aux: ", ind_aux)

            for IHid in range(NHidro):
                if prob_exc_des[IHid] > prob_red[j] and j + 1 < N_Est_Red:
                    j += 1
                IndHid.loc[ind_aux[IHid], cname] = ind_aux1[j]

        # termina ciclo sobre centrales con pronostico de deshielo    

        IndHid_all = pd.DataFrame(-1, index = np.arange(NHidro), columns = NombreCau)

        #aux = df_cen.set_index("CENTRALES").dropna(subset = "Pronóstico Asociado")
        #auxx = df_cen.set_index("CENTRALES")
        #auxx = auxx[(auxx["Pronóstico Asociado"].isna()) & (auxx.index.isin(NombreCau))]

        df_not_desh = df_cen[np.isnan(df_cen["Pronóstico de Deshielo"])] # sin pronostico de deshielo
        df_not_desh_pro_aso = df_not_desh.dropna(subset = "Pronóstico Asociado") # sin pronostico de deshielo con pro aso
        df_not_desh_not_pro_aso = df_not_desh[df_not_desh["Pronóstico Asociado"].isna()] # sin pronostico de deshielo sin pro aso

        # primero nos paseamos por las centrales con pronostico de deshielo 
        cdesh = []
        count = 0
        for cname in df_desh["CENTRALES"]:
            Nom_Est_Pro = cname
            aux2 = IndHid.loc[:,Nom_Est_Pro].values
            dict_ah1[Nom_Est_Pro].loc[:,"INDHID"] = aux2 +1
            IndHid_all.loc[:, Nom_Est_Pro] = aux2 + 1
            cdesh.append(cname)
            count += 1

        #df_desh_aux = df_desh.set_index("CENTRALES")
        # ahora por las que tienen pronóstico asociado
        for k, row in df_not_desh_pro_aso.iterrows():
            pname = row["Pronóstico Asociado"]
            cname = row["CENTRALES"]
            if pname not in NombreCau:
                print("Error. El proceso que asigna la estadística reducida del Pronóstico de Deshielo a centrales asociadas fue suspendido,"+
                      "Central Asociada a central:  ", cname, " , no tiene pronóstico de deshielo o no existe:  ", pname)
            #if cname == "HLH_AZUFRE": print("HOOOOOOLA")
            aux2 = IndHid.loc[:, pname].values
            dict_ah1[cname].loc[:,"INDHID"] = aux2 + 1
            IndHid_all.loc[:, cname] = aux2 + 1
            count += 1

        # ahora las restantes
        for cname in df_not_desh_not_pro_aso.CENTRALES:
            if cname not in NombreCau: continue
            dict_ah1[cname].loc[:, "INDHID"] = np.arange(1, NHidro + 1)
            IndHid_all.loc[:, cname] = np.arange(1, NHidro + 1)
            count += 1

        #print("Total : ", count)

    else:
        IndHid_all = pd.DataFrame(-1, index = np.arange(NHidro), columns = NombreCau)
        aux = df_cen[df_cen["Afluente Estocástico"] == 1.0].set_index("CENTRALES")
        for cname in aux.index:
            dict_ah1[cname].loc[:, "INDHID"] = np.arange(1, NHidro + 1)
            IndHid_all.loc[:, cname] = np.arange(1, NHidro + 1)
            
    
    # Acá comienza formalmente la rutina para las primeras 4 semanas (o eso dice la macro)
    
    # AFLU 4s
    df_cen_afl_est = df_cen[df_cen["Afluente Estocástico"] == 1.0].set_index("CENTRALES")
    #print(df_cen_afl_est.columns.tolist())
    Aflu1s = df_cen_afl_est["Afluente Primera Semana.1"].values
    Aflu2s = df_cen_afl_est["Afluente Segunda Semana"].values
    Aflu3s = df_cen_afl_est["Afluente Tercera Semana"].values
    Aflu4s = df_cen_afl_est["Afluente Cuarta Semana"].values
    Aflu1s_li = df_cen_afl_est["Afluente Primera Semana"].values
    Est_Sem = df_cen_afl_est["Estadística Semanal"].replace(np.nan, 0.0).astype(bool)
    Pron_2s = df_cen_afl_est.iloc[:,33].replace(np.nan, 0.0).astype(bool)
    Nom_Est_Sem = df_cen_afl_est.index.values
    
    dict_qcon = {}
    dict_qcon_aux = {}
    qcon_aux_li = np.zeros(NCenEst).astype('float32')

    # inicializacion
    for i, cname in enumerate(NombreCau):
        j = Nom_Est_Sem.tolist().index(cname)
        #print("Indice Est Sem: ", j, " Central: ", cname, " Indice cen: ", i)
        dict_qcon[cname] = pd.DataFrame(0.0, index = np.arange(NHidro), columns = [str(i+1) for i in range(NEta_Alf4s)], dtype = "float32")
        dict_qcon_aux[cname] = pd.DataFrame(0.0, index = np.arange(NHidro), columns = [str(i+1) for i in range(NEta_Alf4s)], dtype = "float32")

        qcon_aux_li[i] = Aflu1s_li[j]
        dict_qcon[cname].iloc[:, 0] = Aflu1s[j]

        dict_qcon_aux[cname].iloc[:, 0] = Aflu1s[j]
        dict_qcon_aux[cname].iloc[:, 1] = Aflu2s[j]
        dict_qcon_aux[cname].iloc[:, 2] = Aflu3s[j]
        dict_qcon_aux[cname].iloc[:, 3] = Aflu4s[j]

        qeta_pro = dict_qeta_pro[cname]
        qeta_des = dict_qeta_des[cname]
        pbb_exc  = dict_pbb_exc[cname]
        qeta_max = dict_qeta_max[cname]
        qeta_min = dict_qeta_max[cname]
        qeta     = dict_qeta[cname]

        if Est_Sem.iloc[j]:
            #print("\t", cname, " tiene EstSem")
            if Pron_2s.iloc[j]:
                #print("\t\t", cname, " tiene Pron2s")
                ieta_start = 2
                dict_qcon[cname].loc[:,"2"] = qeta.loc[:,"2"]
            else:
                ieta_start = 1

            Ln_Aflu1s = np.log(np.maximum(Aflu1s[j], 0.01))

            for ieta in range(ieta_start, NEta_Alf4s):
                ro = dict_corr[cname].iloc[ieta - 1]
                Media_bi = (qeta_pro.iloc[ieta] + ro * (Ln_Aflu1s - qeta_pro.loc["1"]) * qeta_des.loc[str(ieta + 1)] / qeta_des.loc["1"])
                DesvE_bi = qeta_des.loc[str(ieta+1)] * np.sqrt((1- ro**2))
                #print("ieta: ", ieta, " media: ", Media_bi, " DEsv: ", DesvE_bi, " ro: ", ro, " LnAflu1s: ", Ln_Aflu1s, "str(ieta + 1): ", str(ieta + 1))
                for IHid in range(NHidro):

                    Pbb_Aux = pbb_exc.iloc[IHid, ieta]
                    Afl_Aux = norm.ppf(Pbb_Aux, Media_bi, DesvE_bi)
                    #print("\t Afl_Aux: ", Afl_Aux, " Pbb_Aux: ", Pbb_Aux )
                    dict_qcon[cname].loc[IHid, str(ieta + 1)] = np.maximum(np.minimum(np.exp(Afl_Aux), qeta_max.loc[str(ieta + 1)]),qeta_min.loc[str(ieta + 1)])
        else:

            for ieta in range(2, NEta_Alf4s + 1):
                #print("\t Sin est_sem ", cname, " ieta: ", ieta)
                dict_qcon[cname].loc[:,str(ieta)] = qeta.loc[:,str(ieta)]

    
    ## Pronóstico meteorológico 'qdia' segunda semana
    
    # pronostico meteorologico qdia segunda semana (2s)

    # todas las centrales con pronostico meteorologico 2s
    df_afl2s = df_cen[df_cen.iloc[:,34].replace(np.nan, 0.0).astype(bool)].reset_index(drop = True)
    NCen_2s = len(df_afl2s)
    #print("Numero de centrales con pronostico 2s: ", NCen_2s)

    # todas las centrales con pronostico SPC 2s
    df_aflSPC2s = df_cen[~df_cen.iloc[:,37].isna()].reset_index(drop = True)
    #print("Numero de centrales con pronostico SPC 2s: ", len(df_aflSPC2s))

    if df_fla.loc["Flag Pronóstico 2s"][df_fla.columns[0]]:
        # inicializacion
        Fecha2s_incial = df_eta.loc[1, "Inicial"]
        Fecha2s_final  = df_eta.loc[1, "Final"]
        VolMax_2s = df_afl2s.loc[:, "Volumen Máximo 2S hm3"]
        VolMin_2s = df_afl2s.loc[:, "Volumen Mínimo 2S hm3"]
        MesPro_2s = Fecha2s_incial.month
        IndHid_2s = pd.DataFrame(0, index = np.arange(NHidro), columns = list(df_afl2s.CENTRALES))
        Nom_Est_Pro_2s = df_afl2s.CENTRALES.values
        Nom_Est_ProAso_2s = df_aflSPC2s.loc[:, "Pronóstico SPC Asociado"]
        VolDes_2s = pd.DataFrame(0.0, index = np.arange(NHidro), columns = list(df_afl2s.CENTRALES))
        VolDesAux_2s = None
        VolDesOrd_2s = None
        prob_exc_des_2s = (2* np.arange(1, NHidro + 1) - 1) / (2* NHidro)
        df_vol_desh_2s = pd.DataFrame(0.0, index = np.arange(NHidro), columns = df_afl2s.CENTRALES.tolist(), dtype = 'float32')
        dict_desh_2s_ord_aux = {}
        IndHid_all_2s = pd.DataFrame(-1, index = np.arange(NHidro), columns = NombreCau)

        FechaI2s = (datetime.datetime(Fecha2s_incial.year, Fecha2s_incial.month, Fecha2s_incial.day) - datetime.datetime(Fecha2s_incial.year - 1, 12, 31)).days
        FechaF2s = (datetime.datetime(Fecha2s_final.year, Fecha2s_final.month, Fecha2s_final.day) - datetime.datetime(Fecha2s_final.year - 1, 12, 31)).days


        if Fecha2s_incial.month <= 3:
            bis1_2s = calendar.isleap(Fecha2s_incial.year)
            bis2_2s = False
        else:
            bis1_2s = calendar.isleap(Fecha2s_incial.year)
            bis2_2s = calendar.isleap(Fecha2s_incial.year + 1)

        if FechaI2s > FechaF2s:
            if not bis2_2s:
                FechaF2s = FechaF2s + 365
            else:
                FechaF2s = FechaF2s + 366

        for k, cname in enumerate(df_afl2s.CENTRALES):
            #print("Procesando 2s para ", cname, FechaI2s, FechaF2s)
            vmin        = VolMin_2s[k]
            vmax        = VolMax_2s[k]
            mes_pro     = MesPro_2s
            df_qdia     = dict_qdia[cname]
            df_qdiabis  = dict_qdiabis[cname]


            for IHid in range(NHidro):
                VolAux_2s = 0.0
                qdiah    = df_qdia.iloc[IHid,:].astype('float32')
                qdiahbis = df_qdiabis.iloc[IHid,:].astype('float32')
                #print("\tIHid: ", IHid)
                #print("\t", qdiah[(FechaI2s-1):FechaF2s])
                #print("\t", qdiahbis[(FechaI2s-1):FechaF2s])

                for idia in range(FechaI2s, FechaF2s + 1):
                    #print("\t\t idia, vol2s: ", idia, VolAux_2s)
                    if not bis1_2s:
                        if idia > 365:
                            IDia_a = idia - 365
                        else:
                            IDia_a = idia
                        if bis2_2s and (idia > 365):
                            VolAux_2s += qdiah.iloc[IDia_a - 1] * 0.0864
                        else:
                            VolAux_2s += qdiahbis.iloc[IDia_a - 1] * 0.0864
                    else:
                        if idia > 366:
                            IDia_a = idia - 366
                        else:
                            IDia_a = idia

                        if (not bis2_2s) and (idia > 366):
                            VolAux_2s += qdiah.iloc[IDia_a - 1] * 0.0864
                        else:
                            VolAux_2s += qdiahbis.iloc[IDia_a - 1] * 0.0864

                #print("\tVol2s: ", VolAux_2s)
                df_vol_desh_2s.loc[IHid, cname] = np.float32(VolAux_2s)
            #if cname == "COLBUN": print(df_vol_desh_2s.loc[:, cname])
            dict_desh_2s_ord_aux[cname] = df_vol_desh_2s.loc[:, cname].sort_values(ascending = False)
            #if cname == "COLBUN": print(dict_desh_2s_ord_aux[cname])

            if  dict_desh_2s_ord_aux[cname].iloc[-1] > vmax:
                print("Error: Volumen Máximo período menor que mínimo estadística: ", cname)
            if  dict_desh_2s_ord_aux[cname].iloc[0] < vmin:
                print("Error: Volumen Mínimo período mayor que máximo estadística: ", cname)
            if  vmax < vmin:
                print("Error: Volumen Mínimo período mayor que volumen máximo período: ", cname)

            aux = dict_desh_2s_ord_aux[cname].reset_index(drop = True)

            #if cname  == "COLBUN": print(vmax,cname, aux)
            j = aux[aux - vmax <= 0.0 ].index[0]
            hid_max_2s = j
            if dict_desh_2s_ord_aux[cname].iloc[-1] >= vmin:
                hid_min_2s = NHidro - 1      
            else:
                while (dict_desh_2s_ord_aux[cname].iloc[j] >= vmin and j + 1 < NHidro):
                    j +=1
                hid_min_2s = j - 1

            N_Est_Red_2s = hid_min_2s - hid_max_2s + 1

            #if cname == "COLBUN": print("vmin, vmax, hid_min_2s, hid_max_2s, N_Est_Red_2s :", vmin, vmax, hid_min_2s, hid_max_2s, N_Est_Red_2s)
            if (N_Est_Red_2s == 1):
                print("Error. Estadística reducida a sólo un año: ", cname, hid_min_2s, hid_max_2s)
                #print(aux, vmax, vmin)

            prob_red_2s   = np.zeros(N_Est_Red_2s).astype('float32')
            ind_aux1_2s   = np.zeros(N_Est_Red_2s).astype('int32')

            for IRed in range(N_Est_Red_2s):
                prob_red_2s[IRed] = (IRed + 1) / N_Est_Red_2s
                ind_aux1_2s[IRed] = dict_desh_2s_ord_aux[cname].index[hid_max_2s + IRed]
            #if cname == "COLBUN": print("prob_red_2s: ", prob_red_2s)
            #if cname == "COLBUN": print("ind_aux1_2s: ", ind_aux1_2s)
            #if cname == "COLBUN": print("prob_exc_des_2s: ", prob_exc_des_2s)

            j = 0
            ind_aux_2s = dict_desh_2s_ord_aux[cname].index
            #if cname == "COLBUN": print("ind_aux_2s: ", ind_aux_2s)
            for IHid in range(NHidro):
                if prob_exc_des_2s[IHid] > prob_red_2s[j] and j + 1 < N_Est_Red_2s:
                    j += 1
                IndHid_2s.loc[ind_aux_2s[IHid], cname] = ind_aux1_2s[j] + 1

        # primero centrales con pronostico 2s
        count = 0
        for k, cname in enumerate(Nom_Est_Pro_2s):
            #print("procesando con pro 2s: ", cname)
            aux2s = IndHid_2s.loc[:, cname].values
            dict_ah1[cname].loc[:, "INDHID2S"] = aux2s
            IndHid_all_2s.loc[:, cname] = aux2s
            count += 1
        cc = count
        #print("TOTAL NOM_EST_PRO: ", count)


        # ahora por las que tienen pronóstico asociado SPC
        for k, row in df_aflSPC2s.iterrows():
            pname = row["Pronóstico SPC Asociado"]
            cname = row["CENTRALES"]
            #print("Procesando con pron SPC: ", pname, cname)
            if pname not in NombreCau:
                print("Error. El proceso que asigna la estadística reducida del Pronóstico de Segunda Semana a centrales asociadas fue suspendido,"+
                      "Central Asociada a central:  ", cname, " , no tiene pronóstico  para la segunda semana o no existe:  ", pname)
            aux2_2s = IndHid_2s.loc[:, pname].values
            dict_ah1[cname].loc[:,"INDHID2S"] = aux2_2s
            IndHid_all_2s.loc[:, cname] = aux2_2s

            count += 1

        #print("TOTAL SPC: ", count - cc)
        cc = count    

        # ahora las restantes
        restantes = [cname for cname in NombreCau if (cname not in df_aflSPC2s.CENTRALES) and (cname not in Nom_Est_Pro_2s)]

        for cname in restantes:
            #print("Procesando restantes; ", cname)
            dict_ah1[cname].loc[:, "INDHID2S"] = np.arange(1, NHidro + 1)
            IndHid_all_2s.loc[:, cname] = np.arange(1, NHidro + 1)

            count += 1
        #print("TOTAL Restantes: ", count - cc)

    else:
        IndHid_all_2s = pd.DataFrame(-1, index = np.arange(NHidro), columns = NombreCau)
        aux = df_cen[df_cen["Afluente Estocástico"] == 1.0].set_index("CENTRALES")

        count = 0

        for cname in aux.index:
            dict_ah1[cname].loc[:, "INDHID2S"] = np.arange(1, NHidro + 1)
            IndHid_all_2s.loc[:, cname] = np.arange(1, NHidro + 1)
            count += 1
    # fin 2S    

    #print("Total de centrales procesadas: ", count)
    
    ## Reemplazo de caudales 4s incertidumbre reducida
    
    NEta_Ini_Desh = -1
    NEta_Fin_Desh = -1

    if MesIni < 8 and MesIni > 3:
        Flag_Desh  = False
    else:
        Flag_Desh = True

    #NFil = len(df_eta)
    #Flag_Desh
    
    ### Llenado de MesEta
    
    aux = df_eta["Inicial"].dt.month - 3
    aux.loc[aux[aux <= 0].index] += 12
    aux
    df_eta["IMes"] = aux
    MesEta = np.zeros(NEta).astype('int32')

    ieta = 0
    for irow, row in df_eta.iterrows():
        NBlo = row["Nº Bloques"]
        imes = row["IMes"]
        for iblo in range(NBlo):
            MesEta[ieta] = imes
            if ieta > 0 and Flag_Desh:
                if MesEta[ieta - 1] == 6 and imes == 7:
                    NEta_Ini_Desh = ieta + 1
                elif MesEta[ieta - 1] == 12 and imes == 1:
                    NEta_Fin_Desh = ieta + 1
                    Flag_Desh = False
            ieta += 1
    #print("Flag_Desh: ", Flag_Desh)
    #print("NEta_Ini_Desh: ", NEta_Ini_Desh)
    #print("NEta_Fin_Desh: ", NEta_Fin_Desh)
    #print("MesEta: ", MesEta)
    
    if sim_type == TipoSimulacion.CONDICIONADA4s:
        # primera y segunda semana
        for icau, cname in enumerate(NombreCau):
            dict_ah1[cname].loc[:, "1"] = qcon_aux_li[icau] # todas las hidrologias en 1s
            dict_ah1[cname].loc[:, "2"] = dict_qcon[cname].loc[IndHid_all_2s.loc[:, cname] - 1, "2"].values

        if MesIni <= 8 and MesIni > 3:
            if FlPdD:
                for ieta in range(3, NEta_Alf4s + 1):
                    if ieta > NEta_Ini_Desh and ieta < NEta_Fin_Desh: # uniformizar rangos de nidices 0 o 1 based
                        for icau, cname in enumerate(NombreCau):
                            dict_ah1[cname].loc[:, str(ieta)] =   dict_qcon[cname].loc[IndHid_all.loc[:, cname] - 1, str(ieta)].values 
                    else:
                        for icau, cname in enumerate(NombreCau):
                            dict_ah1[cname].loc[:, str(ieta)] =   dict_qcon[cname].loc[:, str(ieta)].values
            else:
                for ieta in range(3, NEta_Alf4s + 1):
                    for icau, cname in enumerate(NombreCau):
                        #print(cname, dict_qcon[cname])
                        dict_ah1[cname].loc[:, str(ieta)] =   dict_qcon[cname].loc[:, str(ieta)].values
        else:
            for ieta in range(3, NEta_Alf4s + 1):
                if MesEta[ieta] == 9:
                    for icau, cname in enumerate(NombreCau):
                        dict_ah1[cname].loc[:, str(ieta)] =   dict_qcon[cname].loc[:, str(ieta)].values
                elif MesEta[ieta] == 4:
                    for icau, cname in enumerate(NombreCau):
                        dict_ah1[cname].loc[:, str(ieta)] =   dict_qeta[cname].loc[:, str(ieta)].values
                else:
                    # QEta(ICau, IndHid_all(ICau, IHid), ieta)
                    #print(ieta, dict_qeta[cname], IndHid_all.loc[:, cname])
                    for icau, cname in enumerate(NombreCau):
                        dict_ah1[cname].loc[:, str(ieta)] =   dict_qeta[cname].loc[IndHid_all.loc[:, cname] - 1, str(ieta)].values

    elif sim_type == TipoSimulacion.NOCONDICIONADA4s:
        semcols = [str(i) for i in range(1, NEta_Alf4s + 1)]
        if MesIni <= 8 and MesIni > 3:
            for icau, cname in enumerate(NombreCau):
                dict_ah1[cname].loc[:, semcols] = dict_qeta[cname].loc[:, semcols].values
        else:
            for icau, cname in enumerate(NombreCau): 
                dict_ah1[cname].loc[:, "1"] = dict_qeta[cname].loc[:, "1"].values

            for ieta in range(2, NEta_Alf4s + 1):
                if MesEtaCal[ieta - 1] in [4,9]:
                    for icau, cname in enumerate(NombreCau): 
                        dict_ah1[cname].loc[:, str(ieta)] = dict_qeta[cname].loc[:, str(ieta)].values
                else:
                    for icau, cname in enumerate(NombreCau): 
                        dict_ah1[cname].loc[:, str(ieta)] = dict_qeta[cname].loc[IndHid_all[:, cname] - 1, str(ieta)].values

    elif sim_type == TipoSimulacion.PROGMENSUAL4s:
        semcols = [str(i) for i in range(1, NEta_Alf4s + 1)]
        if MesIni <= 8 and MesIni > 3:
            for icau, cname in enumerate(NombreCau):
                dict_ah1[cname].loc[:, semcols] = dict_qcon_aux[cname].loc[:, semcols].values
        else:
            for icau, cname in enumerate(NombreCau): 
                dict_ah1[cname].loc[:, "1"] = dict_qcon_aux[cname].loc[:, "1"].values

            for ieta in range(2, NEta_Alf4s + 1):
                if MesEtaCal[ieta - 1] in [4,9]:
                    for icau, cname in enumerate(NombreCau): 
                        dict_ah1[cname].loc[:, str(ieta)] = dict_qcon_aux[cname].loc[:, str(ieta)].values
                else:
                    for icau, cname in enumerate(NombreCau): 
                        dict_ah1[cname].loc[:, str(ieta)] = dict_qcon_aux[cname].loc[IndHid_all[:, cname] - 1, str(ieta)].values
    
    
    # Rutina asociada a PLPAFL_DH
    
    dict_qsem      = {}
    dict_qsem_ah2  = {}
    dict_qsem_his = {}

    for afl_name in dict_ah1.keys():
        df_ah1_cen = dict_ah1[afl_name]
        df_ah2_cen = dict_ah2[afl_name]
        df_his_cen = dict_his[afl_name]

        dict_qsem[afl_name]      = df_ah1_cen.iloc[:,1:(NSemCDEC + 1)].copy()
        dict_qsem_ah2[afl_name]  = df_ah2_cen.iloc[:,1:(NSemCDEC + 1)].copy()
        dict_qsem_his[afl_name]  = df_his_cen.iloc[:,1:(NSemCDEC + 1)].copy()


    # rellena caudales diarios a aprtir de caudales semanales
    dict_qdia     = {}
    dict_qdia_ah2 = {}
    dict_qdia_his = {}

    NDANO = 365
    cols = []
    nd = 0
    for k, nds in enumerate(NDiaS):
        for j in range(1, nds+1):
            nd += 1
            cname = "d"+str(nd)
            cols.append(cname)


    aux = pd.DataFrame(0.0, index=np.arange(NHidro), columns = cols) 


    for afl_name in dict_ah1.keys():
        df_qsem     = dict_qsem[afl_name]
        df_qsem_ah2 = dict_qsem_ah2[afl_name]
        df_qsem_his = dict_qsem_his[afl_name]
        a = aux.copy()
        b = aux.copy()
        c = aux.copy()
        offset = 0
        # enero a marzo
        for isem, nds in enumerate(NDiaS[36:]):
            vals = np.repeat(df_qsem.iloc[:,(36+isem)].values, nds).reshape(NHidro,nds)
            a.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_ah2.iloc[:,(36+isem)].values, nds).reshape(NHidro,nds)
            b.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_his.iloc[:,(36+isem)].values, nds).reshape(NHidro,nds)
            c.iloc[:,(offset):(offset+nds)] = vals

            offset += nds
        # abril a diciembre
        for isem, nds in enumerate(NDiaS[:36]):
            vals = np.repeat(df_qsem.iloc[:,isem].values, nds).reshape(NHidro,nds)
            a.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_ah2.iloc[:,isem].values, nds).reshape(NHidro,nds)
            b.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_his.iloc[:,isem].values, nds).reshape(NHidro,nds)
            c.iloc[:,(offset):(offset+nds)] = vals

            offset += nds

        #for isem, nds in enumerate
        dict_qdia[afl_name]     = a.copy()
        dict_qdia_ah2[afl_name] = b.copy()
        dict_qdia_his[afl_name] = c.copy()

    # arreglo agno bisiesto
    # hay que hacer una función para esto...
    dict_qdiabis     = {}
    dict_qdiabis_ah2 = {}
    dict_qdiabis_his = {}

    aux = pd.DataFrame(0.0, index=np.arange(NHidro), columns = colsb)
    #print(colsb)

    for afl_name, df_qdia in dict_qdia.items():
        #print(afl_name, len(df_qdia.columns))
        a = aux.copy()
        a.iloc[:,:59] = df_qdia.iloc[:,:59]  # esto queda igual
        a.iloc[:,59:60] = a.iloc[:,58:59]    # dia adicional en febrero
        a.iloc[:,60:] = df_qdia.iloc[:,59:]

        dict_qdiabis[afl_name] = a.copy()

    for afl_name, df_qdia_ah2 in dict_qdia_ah2.items():
        a = aux.copy()
        a.iloc[:,:59] = df_qdia_ah2.iloc[:,:59]  # esto queda igual
        a.iloc[:,59:60] = a.iloc[:,58:59]    # dia adicional en febrero
        a.iloc[:,60:] = df_qdia_ah2.iloc[:,59:]

        dict_qdiabis_ah2[afl_name] = a.copy()

    for afl_name, df_qdia_his in dict_qdia_his.items():
        a = aux.copy()
        a.iloc[:,:59] = df_qdia_his.iloc[:,:59]  # esto queda igual
        a.iloc[:,59:60] = a.iloc[:,58:59]    # dia adicional en febrero
        a.iloc[:,60:] = df_qdia_his.iloc[:,59:]

        dict_qdiabis_his[afl_name] = a.copy()

    '''    
    MesIniHid  = MesIni
    AnoIniHid  = df_eta.loc[0, "Inicial"].year
    FilaChAno2 = NFil
    FilaChAno  = 0
    # esto se puede hacer de mejor manera
    for ieta, row in df_eta.iterrows():
        month = row["Inicial"].month
        year  = row["Inicial"].year
        if month == 4:
            if (month > MesIniHid) and (year in [AnoIniHid, AnoIniHid +1]):
                FilaChAno = ieta
                for ieta2 in range(ieta + 1, NFil):
                    month2 = df_eta.loc[ieta2, "Inicial"].month
                    year2  = df_eta.loc[ieta2, "Inicial"].year
                    if (month2 == 4) and (year2 == year + 1):
                        FilaChAno2 = ieta2
                        break
                break
    '''
    MesIniHid  = MesIni
    AnoIniHid  = df_eta.loc[0, "Inicial"].year
    FilaChAno2 = NFil
    FilaChAno  = 0
    # esto se puede hacer de mejor manera
    for ieta, row in df_eta.iterrows():
        month = row["Inicial"].month
        year  = row["Inicial"].year
        if month == 4 and month > MesIniHid and year == AnoIniHid:
            FilaChAno = ieta
            #print("chano fijado en 1")
            for ifil2 in range(ieta + 1, NFil + 1):
                year2  = df_eta.loc[ifil2, "Inicial"].year
                month2 = df_eta.loc[ifil2, "Inicial"].month
                if month2 == 4 and year + 1 == year2:
                    #print("hola 1")
                    FilaChAno2 = ifil2
                    break
            break
        elif month == 4 and year == AnoIniHid + 1:
            FilaChAno = ieta
            #print("chano fijado en 2")
            for ifil2 in range(ieta + 1, NFil + 1):
                year2  = df_eta.loc[ifil2, "Inicial"].year
                month2 = df_eta.loc[ifil2, "Inicial"].month
                #print("ifil2: ", ifil2, " month2: ", month2, "year2: ", year2)
                if month2 == 4 and year + 1 == year2:
                    #print("hola 2")
                    FilaChAno2 = ifil2
                    break
            break
    
    # esta parte de la rutina quedó más lenta que un bolero... aun no se me ocurre como vectorizar el código...
    dict_qeta = {}

    for icau, cname in enumerate(NombreCau):
        #print(icau, cname)
        df_qdia        = dict_qdia[cname]
        df_qdia_ah2    = dict_qdia_ah2[cname]
        df_qdia_his    = dict_qdia_his[cname]
        df_qdiabis     = dict_qdiabis[cname]
        df_qdiabis_ah2 = dict_qdiabis_ah2[cname]
        df_qdiabis_his = dict_qdiabis_his[cname]

        df_qeta = pd.DataFrame(0.0, index = np.arange(NHidro), columns = [str(i) for i in range(1, NEta + 1)])

        for ihid in range(NHidro):
            ieta = 0
            for ifil in range(FilaChAno):
                #print(ifil)
                fini = df_eta.loc[ifil,"Inicial"]
                ffin = df_eta.loc[ifil,"Final"]
                FechaI = (fini - datetime.datetime(fini.year - 1, 12, 31)).days
                FechaF = (ffin - datetime.datetime(ffin.year - 1, 12, 31)).days
                bisiesto = calendar.isleap(fini.year)

                qmed = 0
                if not bisiesto:
                    NDIAS = 365
                    df    = df_qdia
                else:
                    NDIAS = 366
                    df    = df_qdiabis

                for idia in range(FechaI, FechaF + 1):
                    idia_aux = idia
                    if idia_aux > NDIAS: idia_aux -= NDIAS
                    qmed += df.loc[ihid, "d" + str(idia_aux)]


                qmed /= (FechaF - FechaI + 1)
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    #print("\t", ieta)
                    df_qeta.loc[ihid, str(ieta)] = qmed


            for ifil in range(FilaChAno, FilaChAno2):
                #print(ifil)
                fini = df_eta.loc[ifil,"Inicial"]
                ffin = df_eta.loc[ifil,"Final"]
                FechaI = (fini - datetime.datetime(fini.year - 1, 12, 31)).days
                FechaF = (ffin - datetime.datetime(ffin.year - 1, 12, 31)).days
                bisiesto = calendar.isleap(fini.year)

                qmed = 0
                #print(FechaI, FechaF, fini, ffin, bisiesto)
                if not bisiesto:
                    NDIAS = 365
                    df    = df_qdia_ah2
                else:
                    NDIAS = 366
                    df    = df_qdiabis_ah2

                for idia in range(FechaI, FechaF + 1):
                    idia_aux = idia
                    if idia_aux > NDIAS: idia_aux -= NDIAS
                    qmed += df.loc[ihid, "d" + str(idia_aux)]

                qmed /= (FechaF - FechaI + 1)
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    #print("\t", ieta)
                    df_qeta.loc[ihid, str(ieta)] = qmed

            for ifil in range(FilaChAno2, NFil):
                #print(ifil)
                fini = df_eta.loc[ifil,"Inicial"]
                ffin = df_eta.loc[ifil,"Final"]
                FechaI = (fini - datetime.datetime(fini.year - 1, 12, 31)).days
                FechaF = (ffin - datetime.datetime(ffin.year - 1, 12, 31)).days
                bisiesto = calendar.isleap(fini.year)

                qmed = 0

                if not bisiesto:
                    NDIAS = 365
                    df    = df_qdia_his
                else:
                    NDIAS = 366
                    df    = df_qdiabis_his

                for idia in range(FechaI, FechaF + 1):
                    idia_aux = idia
                    if idia_aux > NDIAS: idia_aux -= NDIAS
                    qmed += df.loc[ihid, "d" + str(idia_aux)]

                qmed /= (FechaF - FechaI + 1)
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    #print("\t", ieta)
                    df_qeta.loc[ihid, str(ieta)] = qmed
        dict_qeta[cname] = df_qeta

    # fin del bolero    
    
    IndHid     = pd.DataFrame(0.0, index = np.arange(NHidro), columns = NombreCau)
    IndHid_2s  = pd.DataFrame(0.0, index = np.arange(NHidro), columns = NombreCau)
    IndHid_spc = pd.DataFrame(0.0, index = np.arange(NHidro), columns = NombreCau)
    for icau, cname in enumerate(NombreCau):
        df_qeta = dict_qeta[cname]
        df_ah1  = dict_ah1[cname]
        for ihid in range(NHidro):
            ieta = 0
            for ifil in range(1, NEta_Alf4s + 1):
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    df_qeta.loc[ihid, str(ieta)] = df_ah1.loc[ihid, str(ifil)]

        IndHid.loc[:, cname]     = pd.to_numeric(df_ah1["INDHID"], errors='coerce').values
        IndHid_spc.loc[:, cname] = pd.to_numeric(df_ah1["INDHID"], errors='coerce').values
        IndHid_2s.loc[:, cname]  = pd.to_numeric(df_ah1["INDHID2S"], errors='coerce').values
        
    
    for icau, cname in enumerate(NombreCau):
        df_qeta = dict_qeta[cname]
        df_ah1  = dict_ah1[cname]
        NBlo1s = df_eta.loc[0,"Nº Bloques"]
        NBlo2s = df_eta.loc[1,"Nº Bloques"]
        for ihid in range(NHidro):
            IEta2s = NBlo1s
            for iblo in range(NBlo2s):
                IEta2s += 1
            df_qeta.loc[ihid, str(IEta2s)] = df_ah1.loc[ihid, "2"]
            
    for cname, df in dict_qeta.items():
        cols = [str(i) for i in range(1, NEta + 1)]
        dict_qeta[cname] = correccion_preredondeo(df, cols, 2, rounding_mode="ROUND_HALF_EVEN")

    dict_qeta_lines = {}
    for cname, df_qeta in dict_qeta.items():
        my_lines = []
        aux = df_qeta.T
        for irow, row in aux.iterrows():
            mes  = MesEta[int(irow) - 1]
            iblo = int(irow)
            line = "  {:03d}".format(mes)+"     "+"{:03d}".format(iblo)
            values = row.values.tolist()
            txt_values = ''.join(["{:>8.2f}" for i in range(len(values))])
            line += txt_values.format(*values)
            my_lines.append(line)
        dict_qeta_lines[cname] = my_lines
        
    return NCau, NHidro, NombreCau, NEta, MesEta, dict_qeta_lines


def parse_afluentes_sin_aflu4s(df_hid_xls: pd.DataFrame, # hoja hidrologia
                    df_ah1_xls: pd.DataFrame, # hoja caudales ah1
                    df_ah2_xls: pd.DataFrame, # hoja caudales ah2
                    df_his_xls: pd.DataFrame, # hoja historicos
                    df_eta_xls: pd.DataFrame, # hoja etapas
                    df_cen_xls: pd.DataFrame, # hoja centrales
                    df_fla_xls: pd.DataFrame, # hoja datos flags especificos
                    sim_type  : TipoSimulacion, # 'flag' de tipo de simulacion
                   ) -> tuple:
    
    
    df_hid = df_hid_xls.copy()
    df_hid = df_hid.drop("Unnamed: 2", axis = 1)
    df_hid.rename(columns = {"Unnamed: 1": "dato", "Unnamed: 3": "valor"}, inplace = True)
    df_hid = df_hid.set_index("dato", drop = True)

    df_ah1 = df_ah1_xls.copy()
    df_ah1 = df_ah1.dropna(subset = "CENTRAL")
    #print(df_ah1)
    df_ah2 = df_ah2_xls.copy()
    df_ah2 = df_ah2.dropna(subset = "CENTRAL")
    #print(df_ah2)
    df_his = df_his_xls.copy()
    df_his = df_his.dropna(subset = "CENTRAL")
    df_eta = df_eta_xls.copy()
    df_eta = df_eta.dropna(subset=['Etapa', 'Nº Bloques'])
    df_eta = df_eta.astype({'Etapa': 'int32', 'Nº Días': 'int32', 'Año': 'int32', 'Nº Bloques': 'int32' })

    df_cen = df_cen_xls.copy()
    df_fla = df_fla_xls.dropna().set_index(df_fla_xls.columns[0], drop = True).astype(bool)
    
    NHidro    = df_hid.loc["Número de Hidrologías", "valor"]
    NCau      = int( len(df_ah1) / NHidro )
    NombreCau = list(df_ah1.CENTRAL.unique())
    MesIniCal = df_eta.loc[0,"Inicial"].month
    NSemCDEC  = 48
    NDiaS     = [ 7, 8, 7, 8, #ABR
                  7, 8, 8, 8, #MAY
                  7, 8, 7, 8, #JUN
                  7, 8, 8, 8, #JUL
                  7, 8, 8, 8, #AGO
                  7, 8, 7, 8, #SEP
                  7, 8, 8, 8, #OCT
                  7, 8, 7, 8, #NOV
                  7, 8, 8, 8, #DIC
                  7, 8, 8, 8, #ENE
                  7, 7, 7, 7, #FEB
                  7, 8, 8, 8] #MAR

    NFil       = len(df_eta)
    NEta       = int(df_eta["Nº Bloques"].sum()) # se mantiene el nombre de la variable de la macro
    NEta_Alf4s = 4
    MesIni     = MesIniCal
    MesEtaCal  = df_eta.loc[0:(NEta_Alf4s - 1), "Inicial"].dt.month
    bisiesto   = calendar.isleap(df_eta.loc[0,"Inicial"].year)
    NCenEst    = int(df_cen["Afluente Estocástico"].sum())
    NCen       = len(df_cen)
    NCen_Pro   = int(df_cen["Pronóstico de Deshielo"].sum()) if MesIni > 7 or MesIni < 4 else -1
    MesIni     = df_eta.loc[0,"Inicial"].month
    FlPdD      = df_fla.loc["Flag Pronóstico Deshielo"].iloc[0] # flag de pronostico de deshielo celda 'Datos'
    NEta4SubP  = df_eta.loc[:(NEta_Alf4s - 1), "Nº Bloques"].sum()    

    # ajuste a indexación año cdec ¿?

    if MesIniCal > 3:
        MesIniC = MesIniCal - 3
    else:
        MesIniC = MesIniCal + 9

    SemAux = (MesIniC - 1)*4
    
    ## Codigo asociado a rutina AFLU4S_DH
    
    dict_ah1 = afluentes_ah_a_diccionario(df_ah1)
    dict_ah2 = afluentes_ah_a_diccionario(df_ah2)
    dict_his = afluentes_ah_a_diccionario(df_his)

# Rutina asociada a PLPAFL_DH
    
    dict_qsem      = {}
    dict_qsem_ah2  = {}
    dict_qsem_his = {}

    for afl_name in dict_ah1.keys():
        df_ah1_cen = dict_ah1[afl_name]
        df_ah2_cen = dict_ah2[afl_name]
        df_his_cen = dict_his[afl_name]

        dict_qsem[afl_name]      = df_ah1_cen.iloc[:,1:(NSemCDEC + 1)].copy()
        dict_qsem_ah2[afl_name]  = df_ah2_cen.iloc[:,1:(NSemCDEC + 1)].copy()
        dict_qsem_his[afl_name] = df_his_cen.iloc[:,1:(NSemCDEC + 1)].copy()


    # rellena caudales diarios a aprtir de caudales semanales
    dict_qdia     = {}
    dict_qdia_ah2 = {}
    dict_qdia_his = {}

    NDANO = 365
    cols = []
    nd = 0
    for k, nds in enumerate(NDiaS):
        for j in range(1, nds+1):
            nd += 1
            cname = "d"+str(nd)
            cols.append(cname)


    aux = pd.DataFrame(0.0, index=np.arange(NHidro), columns = cols) 


    for afl_name in dict_ah1.keys():
        df_qsem     = dict_qsem[afl_name]
        df_qsem_ah2 = dict_qsem_ah2[afl_name]
        df_qsem_his = dict_qsem_his[afl_name]
        a = aux.copy()
        b = aux.copy()
        c = aux.copy()
        offset = 0
        # enero a marzo
        for isem, nds in enumerate(NDiaS[36:]):
            vals = np.repeat(df_qsem.iloc[:,(36+isem)].values, nds).reshape(NHidro,nds)
            a.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_ah2.iloc[:,(36+isem)].values, nds).reshape(NHidro,nds)
            b.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_his.iloc[:,(36+isem)].values, nds).reshape(NHidro,nds)
            c.iloc[:,(offset):(offset+nds)] = vals

            offset += nds
        # abril a diciembre
        for isem, nds in enumerate(NDiaS[:36]):
            vals = np.repeat(df_qsem.iloc[:,isem].values, nds).reshape(NHidro,nds)
            a.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_ah2.iloc[:,isem].values, nds).reshape(NHidro,nds)
            b.iloc[:,(offset):(offset+nds)] = vals

            vals = np.repeat(df_qsem_his.iloc[:,isem].values, nds).reshape(NHidro,nds)
            c.iloc[:,(offset):(offset+nds)] = vals

            offset += nds

        #for isem, nds in enumerate
        dict_qdia[afl_name]     = a.copy()
        dict_qdia_ah2[afl_name] = b.copy()
        dict_qdia_his[afl_name] = c.copy()

    # arreglo agno bisiesto
    # hay que hacer una función para esto...
    dict_qdiabis     = {}
    dict_qdiabis_ah2 = {}
    dict_qdiabis_his = {}

    colsb = cols + ["d366"]
    aux = pd.DataFrame(0.0, index=np.arange(NHidro), columns = colsb)
    #print(colsb)

    for afl_name, df_qdia in dict_qdia.items():
        #print(afl_name, len(df_qdia.columns))
        a = aux.copy()
        a.iloc[:,:59] = df_qdia.iloc[:,:59]  # esto queda igual
        a.iloc[:,59:60] = a.iloc[:,58:59]    # dia adicional en febrero
        a.iloc[:,60:] = df_qdia.iloc[:,59:]

        dict_qdiabis[afl_name] = a.copy()

    for afl_name, df_qdia_ah2 in dict_qdia_ah2.items():
        a = aux.copy()
        a.iloc[:,:59] = df_qdia_ah2.iloc[:,:59]  # esto queda igual
        a.iloc[:,59:60] = a.iloc[:,58:59]    # dia adicional en febrero
        a.iloc[:,60:] = df_qdia_ah2.iloc[:,59:]

        dict_qdiabis_ah2[afl_name] = a.copy()

    for afl_name, df_qdia_his in dict_qdia_his.items():
        a = aux.copy()
        a.iloc[:,:59] = df_qdia_his.iloc[:,:59]  # esto queda igual
        a.iloc[:,59:60] = a.iloc[:,58:59]    # dia adicional en febrero
        a.iloc[:,60:] = df_qdia_his.iloc[:,59:]

        dict_qdiabis_his[afl_name] = a.copy()

    '''    
    MesIniHid  = MesIni
    AnoIniHid  = df_eta.loc[0, "Inicial"].year
    FilaChAno2 = NFil
    FilaChAno  = 0
    # esto se puede hacer de mejor manera
    for ieta, row in df_eta.iterrows():
        month = row["Inicial"].month
        year  = row["Inicial"].year
        if month == 4:
            if (month > MesIniHid) and (year in [AnoIniHid, AnoIniHid +1]):
                FilaChAno = ieta
                for ieta2 in range(ieta + 1, NFil):
                    month2 = df_eta.loc[ieta2, "Inicial"].month
                    year2  = df_eta.loc[ieta2, "Inicial"].year
                    if (month2 == 4) and (year2 == year + 1):
                        FilaChAno2 = ieta2
                        break
                break
    '''
    MesIniHid  = MesIni
    AnoIniHid  = df_eta.loc[0, "Inicial"].year
    FilaChAno2 = NFil
    FilaChAno  = 0
    # esto se puede hacer de mejor manera
    #print(df_eta)
    #print(df_eta.dtypes)
    for ieta, row in df_eta.iterrows():
        month = row["Inicial"].month
        year  = row["Inicial"].year
        if month == 4 and month > MesIniHid and year == AnoIniHid:
            FilaChAno = ieta
            #print("chano fijado en 1")
            for ifil2 in range(ieta + 1, NFil):
                year2  = df_eta.loc[ifil2, "Inicial"].year
                month2 = df_eta.loc[ifil2, "Inicial"].month
                if mont2 == 4 and year + 1 == year2:
                    #print("hola 1")
                    FilaChAno2 = ifil2
                    break
            break
        elif month == 4 and year == AnoIniHid + 1:
            FilaChAno = ieta
            #print("chano fijado en 2")
            for ifil2 in range(ieta + 1, NFil):
                year2  = df_eta.loc[ifil2, "Inicial"].year
                month2 = df_eta.loc[ifil2, "Inicial"].month
                #print("ifil2: ", ifil2, " month2: ", month2, "year2: ", year2)
                if month2 == 4 and year + 1 == year2:
                    #print("hola 2")
                    FilaChAno2 = ifil2
                    break
            break
    
    # esta parte de la rutina quedó más lenta que un bolero... aun no se me ocurre como vectorizar el código...
    dict_qeta = {}

    for icau, cname in enumerate(NombreCau):
        #print(icau, cname)
        df_qdia        = dict_qdia[cname]
        df_qdia_ah2    = dict_qdia_ah2[cname]
        df_qdiabis     = dict_qdiabis[cname]
        df_qdiabis_ah2 = dict_qdiabis_ah2[cname]
        df_qdia_his    = dict_qdia_his[cname]
        df_qdiabis_his = dict_qdiabis_his[cname]

        df_qeta = pd.DataFrame(0.0, index = np.arange(NHidro), columns = [str(i) for i in range(1, NEta + 1)])

        for ihid in range(NHidro):
            ieta = 0
            for ifil in range(FilaChAno):
                #print(ifil)
                fini = df_eta.loc[ifil,"Inicial"]
                ffin = df_eta.loc[ifil,"Final"]
                FechaI = (fini - datetime.datetime(fini.year - 1, 12, 31)).days
                FechaF = (ffin - datetime.datetime(ffin.year - 1, 12, 31)).days
                bisiesto = calendar.isleap(fini.year)

                qmed = 0
                if not bisiesto:
                    NDIAS = 365
                    df    = df_qdia
                else:
                    NDIAS = 366
                    df    = df_qdiabis

                for idia in range(FechaI, FechaF + 1):
                    idia_aux = idia
                    if idia_aux > NDIAS: idia_aux -= NDIAS
                    qmed += df.loc[ihid, "d" + str(idia_aux)]


                qmed /= (FechaF - FechaI + 1)
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    #print("\t", ieta)
                    df_qeta.loc[ihid, str(ieta)] = qmed


            for ifil in range(FilaChAno, FilaChAno2):
                #print(ifil)
                fini = df_eta.loc[ifil,"Inicial"]
                ffin = df_eta.loc[ifil,"Final"]
                FechaI = (fini - datetime.datetime(fini.year - 1, 12, 31)).days
                FechaF = (ffin - datetime.datetime(ffin.year - 1, 12, 31)).days
                bisiesto = calendar.isleap(fini.year)

                qmed = 0
                #print(FechaI, FechaF, fini, ffin, bisiesto)
                if not bisiesto:
                    NDIAS = 365
                    df    = df_qdia_ah2
                else:
                    NDIAS = 366
                    df    = df_qdiabis_ah2

                for idia in range(FechaI, FechaF + 1):
                    idia_aux = idia
                    if idia_aux > NDIAS: idia_aux -= NDIAS
                    qmed += df.loc[ihid, "d" + str(idia_aux)]

                qmed /= (FechaF - FechaI + 1)
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    #print("\t", ieta)
                    df_qeta.loc[ihid, str(ieta)] = qmed

            for ifil in range(FilaChAno2, NFil):
                #print(ifil)
                fini = df_eta.loc[ifil,"Inicial"]
                ffin = df_eta.loc[ifil,"Final"]
                FechaI = (fini - datetime.datetime(fini.year - 1, 12, 31)).days
                FechaF = (ffin - datetime.datetime(ffin.year - 1, 12, 31)).days
                bisiesto = calendar.isleap(fini.year)

                qmed = 0

                if not bisiesto:
                    NDIAS = 365
                    df    = df_qdia_his
                else:
                    NDIAS = 366
                    df    = df_qdiabis_his

                for idia in range(FechaI, FechaF + 1):
                    idia_aux = idia
                    if idia_aux > NDIAS: idia_aux -= NDIAS
                    qmed += df.loc[ihid, "d" + str(idia_aux)]

                qmed /= (FechaF - FechaI + 1)
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    #print("\t", ieta)
                    df_qeta.loc[ihid, str(ieta)] = qmed
        dict_qeta[cname] = df_qeta

    # fin del bolero    
    
    IndHid     = pd.DataFrame(0.0, index = np.arange(NHidro), columns = NombreCau)
    IndHid_2s  = pd.DataFrame(0.0, index = np.arange(NHidro), columns = NombreCau)
    IndHid_spc = pd.DataFrame(0.0, index = np.arange(NHidro), columns = NombreCau)
    for icau, cname in enumerate(NombreCau):
        df_qeta = dict_qeta[cname]
        df_ah1  = dict_ah1[cname]
        for ihid in range(NHidro):
            ieta = 0
            for ifil in range(1, NEta_Alf4s + 1):
                nblo = df_eta.loc[ifil, "Nº Bloques"]
                for iblo in range(nblo):
                    ieta += 1
                    df_qeta.loc[ihid, str(ieta)] = df_ah1.loc[ihid, str(ifil)]

        IndHid.loc[:, cname]     = pd.to_numeric(df_ah1["INDHID"], errors='coerce').values
        IndHid_spc.loc[:, cname] = pd.to_numeric(df_ah1["INDHID"], errors='coerce').values
        IndHid_2s.loc[:, cname]  = pd.to_numeric(df_ah1["INDHID2S"], errors='coerce').values
        
    
    for icau, cname in enumerate(NombreCau):
        df_qeta = dict_qeta[cname]
        df_ah1  = dict_ah1[cname]
        NBlo1s = df_eta.loc[0,"Nº Bloques"]
        NBlo2s = df_eta.loc[1,"Nº Bloques"]
        for ihid in range(NHidro):
            IEta2s = NBlo1s
            for iblo in range(NBlo2s):
                IEta2s += 1
            df_qeta.loc[ihid, str(IEta2s)] = df_ah1.loc[ihid, "2"]
            
    
    ### Llenado de MesEta
    
    aux = df_eta["Inicial"].dt.month - 3
    aux.loc[aux[aux <= 0].index] += 12
    aux
    df_eta["IMes"] = aux
    
    MesEta = np.zeros(NEta).astype('int32')

    ieta = 0
    for irow, row in df_eta.iterrows():
        NBlo = row["Nº Bloques"]
        imes = row["IMes"]
        for iblo in range(NBlo):
            MesEta[ieta] = imes
            ieta += 1
    
    for cname, df in dict_qeta.items():
        cols = [str(i) for i in range(1, NEta + 1)]
        dict_qeta[cname] = correccion_preredondeo(df, cols, 2, rounding_mode="ROUND_HALF_EVEN")

    dict_qeta_lines = {}
    for cname, df_qeta in dict_qeta.items():
        my_lines = []
        aux = df_qeta.T
        for irow, row in aux.iterrows():
            mes  = MesEta[int(irow) - 1]
            iblo = int(irow)
            line = "  {:03d}".format(mes)+"     "+"{:03d}".format(iblo)
            values = row.values.tolist()
            txt_values = ''.join(["{:>8.2f}" for i in range(len(values))])
            line += txt_values.format(*values)
            my_lines.append(line)
        dict_qeta_lines[cname] = my_lines
        
    return NCau, NHidro, NombreCau, NEta, MesEta, dict_qeta_lines 

######## COSTOS DE CENTRALES
# modificado jul2025 -> compatibilidad json
def parse_costos( df_cos_xls: pd.DataFrame, # hoja costos
                  df_eta_xls: pd.DataFrame, # hoja etapas
                  df_cen_xls: pd.DataFrame, # hoja centrales
                  macro_profile=None        # opcional perfil macro
                ) -> tuple:
    
    #df_eta = df_eta_xls.reset_index(drop = True)
    df_eta = df_eta_xls.copy().dropna(subset=['Etapa']) # Conservar mensuales

    # Rellenar Nº Bloques con 1 para las etapas mensuales
    df_eta['Nº Bloques'] = df_eta['Nº Bloques'].fillna(1).astype('int32')
    
    df_eta = df_eta.astype({'Etapa': 'int32', 'Nº Días': 'int32', 'Año': 'int32'})
    df_eta = df_eta[["Etapa", "Inicial", "Nº Días", "Final", "Año", "Mes", "Nº Bloques"]]
    
    df_eta["Inicial"] = pd.to_datetime(df_eta["Inicial"])
    df_eta["Final"] = pd.to_datetime(df_eta["Final"])
    
    #df_cen = df_cen_xls.reset_index(drop = True)
    df_cen = df_cen_xls.copy()
    #df_cos = df_cos_xls.reset_index(drop = True)
    df_cos = df_cos_xls.copy()
    df_cos = df_cos.astype({'CV': 'float64'})
    
    df_cos["DATE1"] = pd.to_datetime(df_cos["DATE1"])
    df_cos["DATE2"] = pd.to_datetime(df_cos["DATE2"])
    
    NCen     = len(df_cen)
    NombreC  = df_cen["CENTRALES"].values
    TipoC    = df_cen["Tipo de Central"].values
    CVarNom  = df_cen["Costo Variable"].values
    FechaINI = df_eta["Inicial"].iloc[0]

    NFil    = len(df_eta)
    NDia    = df_eta["Nº Días"].sum()
    NEta    = df_eta["Nº Bloques"].sum()
    NMan    = len(df_cos)
    
    # llenado de BloEta/imes
    # en la macro imes tiene dimensión NEta, pero se llenan solo segun NFil
    BloEta = np.zeros(NEta).astype('int32')
    imes   = df_eta["Inicial"].dt.month

    i=0
    for irow, row in df_eta.iterrows():
        nblo = row["Nº Bloques"]
        for iblo in range(nblo):
            BloEta[i] = irow + 1
            i += 1
            
    # llenado inicial CVarDia
    CVarDia = pd.DataFrame(0.0, index = np.arange(NDia), columns = NombreC, dtype = 'float64' )
    MantOK  = np.zeros(NCen).astype('bool')
    for k, col in enumerate(NombreC):
        CVarDia[col] = np.float64(CVarNom[k])
    CVarDia.index += 1
    
    for cos_name in df_cos["NAME"].unique():
        aux = np.where(NombreC == cos_name)[0] 
        if aux.size == 0:
            raise ValueError("plpcosce: No se encontró central {} con costo variable en lista de centrales".format(cos_name))
        else:
            icen = aux[0]
            if TipoC[icen] in ["T", "F"]:
                MantOK[icen] = True
                
    pivot = df_cen.reset_index()[['index', 'CENTRALES']]
    aux = pd.merge(pivot[MantOK], df_cos.rename(columns = {'NAME': 'CENTRALES'}), how = 'left', on = 'CENTRALES' )
    aux = aux.dropna(subset = "index")
    
    
    aux['IDiaINI'] = np.maximum((aux['DATE1'] - FechaINI).dt.days + 1, 1)
    aux['IDiaFIN'] = np.minimum(np.maximum((aux['DATE2'] - FechaINI).dt.days + 1, 0), NDia)
    
    MaskDia = pd.DataFrame(False, index = np.arange(NDia), columns = NombreC)
    MaskDia.index += 1

    for _, row in aux.iterrows():
        icen    = row['index']
        cv      = row['CV']
        IDiaINI = row['IDiaINI']
        IDiaFIN = row['IDiaFIN']
        CVarDia.iloc[(IDiaINI-1):IDiaFIN, int(icen)] = cv
        
        # La macro VBA omite CUALQUIER período donde el costo variable (redondeado a 2 decimales)
        # es igual al costo nominal (redondeado a 2 decimales).
        nom_r = round(float(CVarNom[int(icen)]), 2)
        cv_r  = round(float(cv), 2)
        if cv_r != nom_r:
            MaskDia.iloc[(IDiaINI-1):IDiaFIN, int(icen)] = True

        
    CVarEta = pd.DataFrame(np.nan, index = np.arange(NFil), columns = NombreC).astype('float64', errors = 'ignore')
    MaskEta = pd.DataFrame(False, index = np.arange(NFil), columns = NombreC)

    df_eta['IDiaINI'] = np.maximum((df_eta['Inicial'] - FechaINI).dt.days + 1, 1)
    df_eta['IDiaFIN'] = np.maximum((df_eta['Final'] - FechaINI).dt.days + 1, 0)
    
    for ifil, row in df_eta.iterrows():
        IDiaINI = row['IDiaINI']
        IDiaFIN = row['IDiaFIN']
        for _, row2 in pivot[MantOK].iterrows():
            icen  = row2['index']
            cname = row2['CENTRALES']
            CVarEta.iloc[ifil, int(icen)] = CVarDia.iloc[(IDiaINI-1):IDiaFIN, icen].mean()
            MaskEta.iloc[ifil, int(icen)] = MaskDia.iloc[(IDiaINI-1):IDiaFIN, icen].any()
            
    MantCen    = pd.DataFrame(0, index = np.arange(NFil), columns = NombreC).astype('int32')
    NombreC    = pd.Series(NombreC) # para recuperar indice de central
    CenMant    = NombreC[MantOK]
    CVarAux    = CVarEta[CenMant]
    
    for icen, cname in CenMant.items():
        MantCen.loc[:, cname] = MaskEta.loc[:, cname].astype('int32')

    NEtaCen = MantCen.sum()
    IMant = ((MantOK) * (NEtaCen > 0)).sum()
    
    # esto para evitar meter logica en el template
    imes_aux = (imes + 9) % 12
    imes_aux[imes_aux == 0] = 12
    
    # esto para preprar los contenedores
    CenNomFinal = NombreC[((MantOK) * (NEtaCen > 0)).values]
    
    dict_MantCen = {cname: MantCen[cname].values for cname in CenNomFinal}
    dict_CVarEta = {cname: CVarEta[cname].values for cname in CenNomFinal}
    etapa_list = df_eta['Etapa'].values.astype('int32')
    
    return  NFil, dict_CVarEta, CenNomFinal, NEtaCen[((MantOK) * (NEtaCen > 0)).values], dict_MantCen, IMant, imes_aux, etapa_list
    
######## MANTENIMIENTOS EMBALSES
# modificado jul2025 --> compatibilidad json
def parse_embalses(df_emb_xls: pd.DataFrame, # hoja embalses
                   df_eta_xls: pd.DataFrame, # hoja etapas
                   df_cen_xls: pd.DataFrame  # hoja centrales
                  ) -> tuple:
    
    #df_eta = df_eta_xls.reset_index(drop = True)
    df_eta = df_eta_xls.copy()
    df_eta = df_eta.dropna(subset=['Etapa', 'Nº Bloques'])
    df_eta = df_eta.astype({'Etapa': 'int64', 'Nº Días': 'int64', 'Año': 'int64', 'Nº Bloques': 'int64' })
    df_eta = df_eta[["Etapa", "Inicial", "Nº Días", "Final", "Año", "Mes", "Nº Bloques"]]
    
    df_eta["Inicial"] = pd.to_datetime(df_eta["Inicial"])
    df_eta["Final"] = pd.to_datetime(df_eta["Final"])

    df_cen = df_cen_xls.copy()

    df_emb = df_emb_xls.copy()
    
    #if 'Unnamed: 0' in df_emb.columns:
    #    df_emb = df_emb.drop("Unnamed: 0", axis = 1)
    
    df_emb = df_emb[["EMBALSE","INICIAL","FINAL","MÍNIMA","MÁXIMA"]]

    df_emb = df_emb.dropna(how = 'all').dropna(how = 'any')
    df_emb = df_emb.astype({"MÍNIMA": 'float64', "MÁXIMA": 'float64'})
    
    df_emb["INICIAL"] = pd.to_datetime(df_emb["INICIAL"])
    df_emb["FINAL"] = pd.to_datetime(df_emb["FINAL"])
    

    NFil  = len(df_eta)
    NDia  = df_eta["Nº Días"].sum()
    NEta  = NFil
    NMant = len(df_emb)

    FechaINI = df_eta.loc[0, "Inicial"]
    
    df_eta["IDiaINI"] = np.maximum((df_eta["Inicial"] - FechaINI).dt.days + 1, 1).astype('int64')
    df_eta["IDiaFIN"] = np.maximum((df_eta["Final"] - FechaINI).dt.days + 1, 0).astype('int64')
    df_eta["IMes"]    = df_eta["Inicial"].dt.month.astype('int64')

    cen_cols = ["CENTRALES", "Mínima", "Máxima", "Mínimo", "Máximo"]

    df_cen = df_cen[df_cen["Tipo de Central"] == 'E'][cen_cols].astype({"Mínima": 'float64', "Máxima": 'float64', "Mínimo": 'float64', "Máximo": 'float64'})
    vol_max_safe = df_cen['Máximo'].clip(lower=1.0)
    df_cen["FEscala"] = np.power(10.0, np.int64(np.log10(df_cen['Máximo']) + 0.5)).astype('float64')

    NomEmb = df_cen["CENTRALES"].unique() # lista desde pestaña de centrales
    NEmb   = len(df_cen)
    MantOK = pd.Series(np.zeros(NEmb).astype(bool))

    VMin = pd.DataFrame(0.0, index = np.arange(NDia), columns = NomEmb , dtype = 'float64')
    VMax = pd.DataFrame(0.0, index = np.arange(NDia), columns = NomEmb , dtype = 'float64')
    
    for irow, row in df_cen.iterrows():
        ename = row["CENTRALES"]
        VMin.loc[:,ename] = row["Mínimo"]
        VMax.loc[:,ename] = row["Máximo"]
        
    # chequeo de existencia
    EmbMantNames = pd.Series(df_emb["EMBALSE"].unique())

    for imanem, ename in EmbMantNames.items():
        aux = np.where(NomEmb == ename)[0]
        if aux.size == 0:
            raise ValueError("Error al ejecutar PLPMANEM.DAT: {} no está en la lista de embalses del sistema")
        iemb = aux[0]
        MantOK[iemb] = True # MantOK lleva la indexación sobre la pestaña de centrales
        
    funcdec = Embalses()

    def vols(x, name_col, cota_col) -> np.float64:
        ename = x[name_col].lower()
        cota  = x[cota_col]
        return funcdec.volumen(ename, cota)

    # dataframe de mantenimientos de embalses
    df_emb['volmin'] = df_emb.apply(vols, name_col = 'EMBALSE', cota_col = 'MÍNIMA', axis = 1).astype('float64')
    df_emb['volmax'] = df_emb.apply(vols, name_col = 'EMBALSE', cota_col = 'MÁXIMA', axis = 1).astype('float64')

    df_emb["IDiaINI"] = np.maximum((df_emb["INICIAL"] - FechaINI).dt.days + 1, 1).astype('int64')
    df_emb["IDiaFIN"] = np.minimum(np.maximum((df_emb["FINAL"] - FechaINI).dt.days + 1, 0), NDia).astype('int64')

    df_emb = df_emb[(df_emb.IDiaINI > 0) & (df_emb.IDiaFIN > 0)]
    #df_emb = df_emb[(df_emb.IDiaFIN > df_emb.IDiaIni)]
    df_emb = df_emb.merge(df_cen.rename(columns = {"CENTRALES": "EMBALSE"})[["EMBALSE","FEscala"]], on = 'EMBALSE', how = 'left')
    df_emb['FEscala'] = df_emb['FEscala'].fillna(1.0).replace(0.0, 1.0)
    
    for irow, row in df_emb.iterrows():
        imant   = irow
        iname   = row["EMBALSE"]
        IDiaINI = row["IDiaINI"]
        IDiaFIN = row["IDiaFIN"]
        vmin    = row['volmin']
        vmax    = row['volmax']

        VMin.loc[(IDiaINI-1):(IDiaFIN - 1),iname] = vmin
        VMax.loc[(IDiaINI-1):(IDiaFIN - 1),iname] = vmax
        
    VMinEta = pd.DataFrame(-1.0, index = np.arange(NEta), columns = NomEmb, dtype = 'float64')
    VMaxEta = pd.DataFrame(-1.0, index = np.arange(NEta), columns = NomEmb, dtype = 'float64')

    for irow, mrow in df_emb.iterrows():
        ieta = 0
        mname = mrow["EMBALSE"]
        FEsc  = mrow["FEscala"]
        
        for jrow, erow in df_eta.iterrows():
            
            IDiaINI  = erow["IDiaINI"]
            IDiaFIN  = erow["IDiaFIN"]
            
            Vminprom = VMin.loc[(IDiaINI-1):(IDiaFIN - 1), mname].mean() / FEsc
            Vmaxprom = VMax.loc[(IDiaINI-1):(IDiaFIN - 1), mname].mean() / FEsc

            ieta = jrow
            VMinEta.loc[ieta, mname] = Vminprom
            VMaxEta.loc[ieta, mname] = Vmaxprom
            
    MantCen = pd.DataFrame(False, index = np.arange(NEta), columns = NomEmb)
    MantCen.loc[:, EmbMantNames.tolist()] = True
    IMant = MantOK.sum()
    
    df_manemb_show = pd.DataFrame(columns = ["EMBALSE", "INICIAL", "FINAL", "MÍNIMO", "MÁXIMO"])
    embnames = [e for e in NomEmb if e in EmbMantNames.tolist()]

    for ename in embnames:
        mask           = MantCen[ename]
        IEtas          = MantCen[ename][MantCen[ename]].index

        if IEtas.empty: continue

        ieta = IEtas[0]

        data = []
        while ieta < NEta:
            if ieta not in IEtas: 
                ieta += 1
                continue
            for jeta in range(ieta, NEta):
                CondMin  = abs(VMinEta.loc[ieta, ename] - VMinEta.loc[jeta, ename]) < 0.00000005
                CondMax  = abs(VMaxEta.loc[ieta, ename] - VMaxEta.loc[jeta, ename]) < 0.00000005
                if not (CondMin and CondMax):
                    jeta -= 1
                    break
            data.append([ename, ieta + 1, jeta + 1, VMinEta.loc[ieta, ename], VMaxEta.loc[ieta, ename]])
            ieta = jeta + 1
        aux   = pd.DataFrame(data, columns = ["EMBALSE", "INICIAL", "FINAL", "MÍNIMO", "MÁXIMO"])
        aux   = aux.astype({"EMBALSE": str, "INICIAL": 'int64', "FINAL": 'int64', "MÍNIMO": 'float64', "MÁXIMO": 'float64'})

        if df_manemb_show.empty:
            df_manemb_show = aux.copy()
        else:
            df_manemb_show = pd.concat([df_manemb_show, aux], ignore_index = True)
            
    # hay que generar la función "mock" en la que eventualmente el usuario modifica mant_lin_show
    def user_mod_mantemb(df_mantemb_ini: pd.DataFrame) -> pd.DataFrame:
        # aca se debe mandar la info del argumento a la interfaz de usuario y traer de vuelta 
        # la información eventualmente modificada

        # por ahora, no se hace nada.
        return df_mantemb_ini.copy()
    
    df_mantemb_fin = user_mod_mantemb(df_manemb_show)
    
    names_mantemb = df_mantemb_fin["EMBALSE"].unique().tolist()
    NEmb_final   = len(names_mantemb)
    df_eta["IMes"] = (df_eta["IMes"] + 9) % 12
    df_eta.loc[df_eta["IMes"] == 0, "IMes"] = 12
    data_eta = df_eta[["Etapa", "IMes"]].values
    
    ManEmbEta   = pd.DataFrame(False, index = np.arange(NEta), columns = NomEmb)
    #ManEmbOK   = pd.Series(False, index = np.arange(NEmb))
    VMinEtaFin  = pd.DataFrame(0.0, index = np.arange(NEta), columns = NomEmb)
    VMaxEtaFin  = pd.DataFrame(0.0, index = np.arange(NEta), columns = NomEmb)


    for irow, row in df_mantemb_fin.iterrows():   
        mname = row["EMBALSE"]
        iemb  = np.where(NomEmb == mname)[0][0]
        Ini   = row["INICIAL"]
        Fin   = row["FINAL"]
        vmin  = row["MÍNIMO"]
        vmax  = row["MÁXIMO"]
        ManEmbEta.loc[(Ini - 1):(Fin - 1), mname] = True
        VMinEtaFin.loc[(Ini - 1):(Fin - 1), mname] = vmin
        VMaxEtaFin.loc[(Ini - 1):(Fin - 1), mname] = vmax

    NEtaMantEMb = ManEmbEta.sum()[ManEmbEta.sum() > 0]
    
    my_dict = {}
    for ename, nmant in NEtaMantEMb.items():
        #print(nmant)
        my_dict[ename]  = {'NMANT': nmant}
        mask = ManEmbEta[ename]
        aux = pd.DataFrame(columns = ["mes", "etapa","min", "max"])
        aux[["mes", "etapa"]] = data_eta[mask]
        aux["min"] = VMinEtaFin.loc[mask, ename].values
        aux["max"] = VMaxEtaFin.loc[mask, ename].values
        my_dict[ename]["DATA"] = aux.values
        
    return my_dict, len(NEtaMantEMb)

######## MANTENIMIENTOS EMBALSESH
# modificado jul2025 --> compatibilidad json
def parse_embalsesh(df_emh_xls: pd.DataFrame, # hoja embalsesh
                    df_eta_xls: pd.DataFrame, # hoja etapas
                    df_cen_xls: pd.DataFrame  # hoja centrales
                   ) -> tuple:
    
    #df_eta = df_eta_xls.reset_index(drop = True)
    df_eta = df_eta_xls.copy()
    df_eta = df_eta.dropna(subset=['Etapa', 'Nº Bloques'])
    df_eta = df_eta.astype({'Etapa': 'int64', 'Nº Días': 'int64', 'Año': 'int64', 'Nº Bloques': 'int64' })
    df_eta = df_eta[["Etapa", "Inicial", "Nº Días", "Final", "Año", "Mes", "Nº Bloques"]].copy()
    
    df_eta["Inicial"] = pd.to_datetime(df_eta["Inicial"])
    df_eta["Final"] = pd.to_datetime(df_eta["Final"])

    FechaINI = df_eta.loc[0, "Inicial"]
    NFil  = len(df_eta)
    NDia  = df_eta["Nº Días"].sum()
    NEta  = NFil
    



    df_cen = df_cen_xls.copy()
    if 'Unnamed: 1' in df_cen.columns:
        df_cen = df_cen.rename(columns={'Unnamed: 1': 'CENTRALES'})
    if 'CENTRALES' in df_cen.columns:
        df_cen['CENTRALES'] = df_cen['CENTRALES'].astype(str).str.strip()

    df_emh            = df_emh_xls.copy()
    if 'EMBALSE' in df_emh.columns:
        df_emh['EMBALSE'] = df_emh['EMBALSE'].astype(str).str.strip()
    
    df_emh            = df_emh.dropna(how = 'all').dropna(how = 'any')
    NMant             = len(df_emh)
    #df_emh            = df_emh.astype({"INICIAL":'datetime64[ns]', "FINAL":'datetime64[ns]'})
    df_emh["INICIAL"] = pd.to_datetime(df_emh["INICIAL"])
    df_emh["FINAL"]   = pd.to_datetime(df_emh["FINAL"])
    
    df_emh["IDiaIni"] = np.maximum((df_emh["INICIAL"] - FechaINI).dt.days + 1, 1)
    df_emh["IDiaFin"] = np.minimum(np.maximum((df_emh["FINAL"] - FechaINI).dt.days + 1, 0), NDia)
    
    #df_emb            = df_emb_xls.copy()
    
    funcdec = Embalses()

    def vols(x, name_col, cota_col) -> np.float64:
        ename = x[name_col].lower()
        cota  = x[cota_col]
        return funcdec.volumen(ename, cota)

    #print(df_emh)
    df_emh['volmin'] = df_emh.apply(vols, name_col = 'EMBALSE', cota_col = 'COTA [msnm]', axis = 1)
    
    df_eta["IDiaIni"] = np.maximum((df_eta["Inicial"] - FechaINI).dt.days + 1, 1).astype('int64')
    df_eta["IDiaFin"] = np.maximum((df_eta["Final"] - FechaINI).dt.days + 1, 0).astype('int64')
    df_eta["IMes"]    = df_eta["Inicial"].dt.month.astype('int64')
    df_eta["IMesF"]   = (df_eta["IMes"] + 9) % 12
    df_eta.loc[df_eta["IMesF"] == 0, "IMesF"] = 12

    cen_cols = ["CENTRALES", "Mínima", "Máxima", "Mínimo", "Máximo"]

    df_cen = df_cen[df_cen["Tipo de Central"] == 'E'][cen_cols].astype({"Mínima": 'float64', "Máxima": 'float64', "Mínimo": 'float64', "Máximo": 'float64'})
    vol_max_safe = df_cen['Máximo'].clip(lower=1.0)
    df_cen["FEscala"] = np.power(10.0, np.int64(np.log10(df_cen['Máximo']) + 0.5)).astype('float64')

    df_emh = df_emh[(df_emh.IDiaIni > 0) & (df_emh.IDiaFin > 0)]
    df_emh = df_emh.merge(df_cen.rename(columns = {"CENTRALES": "EMBALSE"})[["EMBALSE","FEscala", "Mínimo"]], on = 'EMBALSE', how = 'left')


    NomEmb = df_cen["CENTRALES"].unique() # lista desde pestaña de centrales
    NEmb   = len(df_cen)
    MantOK = pd.Series(np.zeros(NEmb).astype(bool))
    
    VMin = pd.DataFrame(0.0, np.arange(NDia), columns = NomEmb)
    Costo = pd.DataFrame(0.0, np.arange(NDia), columns = NomEmb)
    
    for irow, row in df_cen.iterrows():
        ename               = row["CENTRALES"]
        vmin                = row["Mínimo"]
        VMin.loc[:, ename]  = vmin
        
    # aca se obvió parte del código de la macro ya que hacia referencias a celdas vacías en el excel
    # el código en cuestion pareciera hacer referencia a que los datos en la pestaña de mantemh estaban en volumenes no cotas
    # HAY QUE CONFIRMAR SI ESO SE USA O NO (lo que estaba en la macro)
    for irow, row in df_emh.iterrows():
        ename   = row['EMBALSE']
        idiaini = row["IDiaIni"]
        idiafin = row["IDiaFin"]
        vmin    = row["volmin"]
        costo   = row["COSTO"]
        VMin.loc[(idiaini - 1):(idiafin - 1), ename]  = vmin
        Costo.loc[(idiaini - 1):(idiafin - 1), ename] = costo
        
    VMinEta  = pd.DataFrame(0.0, index = np.arange(NEta), columns = NomEmb)
    CostoEta = pd.DataFrame(0.0, index = np.arange(NEta), columns = NomEmb)
    
    for irow, row in df_eta.iterrows():
        IDiaINI = row["IDiaIni"]
        IDiaFIN = row["IDiaFin"]

        for irow2, row2 in df_emh.iterrows():
            ename = row2["EMBALSE"]
            FEsc  = row2["FEscala"]
            # Si FEsc llega en 0 o nulo, lo forzamos a 1.0 justo antes de dividir
            if pd.isna(FEsc) or FEsc == 0.0:
                FEsc = 1.0
            VMinEta.loc[irow, ename] = VMin.loc[(IDiaINI - 1):(IDiaFIN - 1), ename].mean() / FEsc
            CostoEta.loc[irow, ename] = Costo.loc[(IDiaINI - 1):(IDiaFIN - 1), ename].mean()
    
    MantCen = pd.DataFrame(False, index = np.arange(NEta), columns = NomEmb)
    # Filtro ORIGINAL: solo embalses con entradas válidas en el período de estudio
    aux     = df_cen[df_cen["CENTRALES"].isin(df_emh["EMBALSE"].unique())]
    for irow, row in aux.iterrows():
        ename   = row["CENTRALES"]
        vminnom = row["Mínimo"]
        FEsc    = row["FEscala"]
        
        CondMin = np.abs(VMinEta[ename] - vminnom /FEsc) < 0.00000005
        
        if np.any(~(CondMin)):
            MantCen.loc[~CondMin, ename] = True

    NEmbMant = len(aux)
    idx_unicos = aux["CENTRALES"].unique()
    NMantEmbMant = MantCen.sum().loc[idx_unicos].copy()
    
    # Detectar embalses presentes en MantEMBh (pre-filtro de fechas) que no tienen
    # entradas válidas en el período → agregarlos con NMANT=0.
    # Ejemplo: RALCO aparece en la hoja pero sus fechas quedan fuera del horizonte.
    emb_prefilter = df_emh_xls.dropna(how='all').dropna(how='any')
    if 'EMBALSE' in emb_prefilter.columns:
        emb_prefilter = emb_prefilter.copy()
        emb_prefilter['EMBALSE'] = emb_prefilter['EMBALSE'].astype(str).str.strip()
        for emb_name in emb_prefilter['EMBALSE'].unique():
            if emb_name not in NMantEmbMant.index and emb_name in MantCen.columns:
                NMantEmbMant[emb_name] = 0
    
    return NMantEmbMant, MantCen, df_eta, VMinEta, CostoEta

######## MANTENIMIENTOS LINEAS
# ediatdo may2025
#editado jul2025 --> compatibilidad json , mantenimientos adicionales

def parse_mlineas(df_lin_xls: pd.DataFrame, # hoja lineas
                  df_mli_xls: pd.DataFrame, # hoja mantli
                  df_eta_xls: pd.DataFrame, # hoja etapas
                  df_cen_xls: pd.DataFrame, # hoja centrales
                  df_ml2_xls: pd.DataFrame, # hoja mantli
                  ) -> tuple:
    
    #df_eta = df_eta_xls.reset_index(drop = True)
    df_eta = df_eta_xls.copy()
    df_eta = df_eta.dropna(subset=['Etapa', 'Nº Bloques'])
    df_eta = df_eta.astype({'Etapa': 'int32', 'Nº Días': 'int32', 'Año': 'int32', 'Nº Bloques': 'int32' })
    df_eta = df_eta[["Etapa", "Inicial", "Nº Días", "Final", "Año", "Mes", "Nº Bloques"]]

    df_eta["Inicial"] = pd.to_datetime(df_eta["Inicial"])
    df_eta["Final"] = pd.to_datetime(df_eta["Final"])
    
    df_cen = df_cen_xls.copy()

    df_lin = df_lin_xls.reset_index(drop = True)
    df_lin = df_lin.dropna(how = 'all').dropna(how = 'any')
    df_lin = df_lin.astype({"A->B": 'float64', "B->A": 'float64', 'Operativa': 'bool' })

    #print("lineas:", df_lin)
    
    df_mli = df_mli_xls.copy()
    df_mli = df_mli.astype({'A-B': 'float64', 'B-A': 'float64', 'OPERATIVA': bool})
    
    df_mli = df_mli[["LÍNEA","INICIAL","FINAL","A-B","B-A","OPERATIVA"]]
    
    
    df_mli = df_mli.dropna(how = 'all').dropna(how = 'any')
    
    #print("mantenimientos ", df_mli)
    
    df_ml2 = df_ml2_xls.copy()
    
    NLin  = len(df_lin)
    NFil  = len(df_eta)
    NDia  = df_eta["Nº Días"].sum()
    NEta  = df_eta["Nº Bloques"].sum()
    NMant = len(df_mli)

    NomLin   = pd.Series(df_lin["Nombre A->B"].values)
    PnomAB   = pd.Series(df_lin["A->B"].values).astype('float32')
    PnomBA   = pd.Series(df_lin["B->A"].values).astype('float32')
    EstnomL  = pd.Series(df_lin["Operativa"].values).astype(bool)
    FechaINI = df_eta.loc[0, "Inicial"]
    
    # dataframes auxiliares, se matienen los nombres de las macros
    PotMaxAB = pd.DataFrame(0.0, index = np.arange(NDia), columns = NomLin, dtype = 'float64')
    PotMaxBA = pd.DataFrame(0.0, index = np.arange(NDia), columns = NomLin, dtype = 'float64')
    PotMinAB = pd.DataFrame(0.0, index = np.arange(NDia), columns = NomLin, dtype = 'float64')
    EstDiaL  = pd.DataFrame(False, index = np.arange(NDia), columns = NomLin, dtype = bool)
    MantOK   = pd.Series(False, index = np.arange(NLin), dtype = bool)
    
    for ilin, lname in enumerate(PotMaxAB.columns):
        PotMaxAB.loc[:,lname] = df_lin.loc[ilin,"A->B"]
        PotMaxBA.loc[:,lname] = df_lin.loc[ilin,"B->A"]
        EstDiaL.loc[:,lname]  = df_lin.loc[ilin,"Operativa"]
        
    for mname in df_mli["LÍNEA"]:
        aux = np.where(NomLin == mname)[0]
        if aux.size == 0:
            raise ValueError("plpmanli: No se encontró línea {} con mantenimiento en lista de lineas".format(mname))
        else:
            ilin = aux[0]
            MantOK[ilin] = True
            
    df_mli_aux = df_mli.copy()
    
    #print(df_mli_aux)
    
    df_mli_aux["INICIAL"] = pd.to_datetime(df_mli_aux["INICIAL"])
    df_mli_aux["FINAL"] = pd.to_datetime(df_mli_aux["FINAL"])
    
    df_mli_aux["IDiaINI"] = np.maximum((df_mli_aux["INICIAL"] - FechaINI).dt.days + 1, 1)
    df_mli_aux["IDiaFIN"] = np.minimum(np.maximum((df_mli_aux["FINAL"] - FechaINI).dt.days + 1, 0), NDia)

    df_eta_aux = df_eta.copy()
    df_eta_aux["IDiaINI"] = np.maximum((df_eta_aux["Inicial"] - FechaINI).dt.days + 1, 1)
    df_eta_aux["IDiaFIN"] = np.maximum((df_eta_aux["Final"] - FechaINI).dt.days + 1, 0)
    
    AuxMantOK = MantOK[MantOK]
    for ilin, _  in AuxMantOK.items():
        lname = df_lin.loc[ilin, "Nombre A->B"]
        aux = df_mli_aux[df_mli_aux["LÍNEA"] == lname]
        if aux.empty:
            print("Hola {}".format(lname))
            continue
        else:

            for imant, row in aux.iterrows():
                IDiaINI = row["IDiaINI"]
                IDiaFIN = row["IDiaFIN"]
                PotMaxAB.loc[(IDiaINI - 1):(IDiaFIN - 1), lname] = row["A-B"]
                PotMaxBA.loc[(IDiaINI - 1):(IDiaFIN - 1), lname] = row["B-A"]
                EstDiaL.loc[(IDiaINI - 1):(IDiaFIN - 1), lname]  = row["OPERATIVA"]
                
    PABEta = pd.DataFrame(0.0, index = np.arange(NEta), columns = NomLin, dtype = 'float64')
    PBAEta = pd.DataFrame(0.0, index = np.arange(NEta), columns = NomLin, dtype = 'float64')
    EstEta = pd.DataFrame(0.0, index = np.arange(NEta), columns = NomLin, dtype = 'bool')

    AuxNomLin = NomLin[MantOK]
    
    for ilin, lname  in AuxNomLin.items():
        ieta = 0
        for ifil, row in df_eta_aux.iterrows():
            IDiaINI = row["IDiaINI"]
            IDiaFIN = row["IDiaFIN"]
            nblo    = row["Nº Bloques"]
            pbaprom = 0.0
            pabprom = 0.0
            estprom = 0
            diaprom = 0

            for idia in range(IDiaINI - 1, IDiaFIN):
                if EstDiaL.loc[idia, lname]:
                    pabprom += PotMaxAB.loc[idia, lname]
                    pbaprom += PotMaxBA.loc[idia, lname]
                    estprom += 1
                    diaprom += 1
                else:
                    estprom -= 1
            if diaprom > 0:
                pabprom /= diaprom
                pbaprom /= diaprom

            for iblo in range(nblo):
                PABEta.loc[ieta, lname] = np.float64(pabprom)
                PBAEta.loc[ieta, lname] = np.float64(pbaprom)
                EstEta.loc[ieta, lname] = (estprom >= 0)
                ieta += 1

    IMant = np.sum(MantOK)
    
    # cuenta el número de etapas con mantenimiento
    MantLin = pd.DataFrame(False, index = np.arange(NEta), columns = NomLin)

    for ilin, lname in AuxNomLin.items():
        CondAB  = np.abs(PABEta[lname] - PnomAB[ilin]) < 0.05
        CondBA  = np.abs(PBAEta[lname] - PnomBA[ilin]) < 0.05
        CondEst = (EstEta.loc[:,lname] == EstnomL[ilin])
        mask = ~(CondAB & CondBA & CondEst)
        if mask.sum() > 0:
            MantLin.loc[mask, lname] = True
            
    df_manlin_show = pd.DataFrame(columns = ["LINEA", "INICIAL", "FINAL", "A-B", "B-A", "OPERATIVA"])

    # primera generacion de datos --> tabla en excel
    IEtas = None
    imant = 0
    for ilin, lname in AuxNomLin.items():

        mask           = MantLin[lname]
        IEtas          = MantLin[lname][MantLin[lname]].index

        if IEtas.empty: continue

        ieta = IEtas[0]
        PABEtaAux = PABEta[lname]
        PBAEtaAux = PBAEta[lname]
        EstEtaAux = EstEta[lname]

        data = []
        while ieta < NEta:
            if ieta not in IEtas: 
                ieta += 1
                continue
            for jeta in range(ieta, NEta):
                CondAB  = abs(PABEtaAux[ieta] - PABEtaAux[jeta]) < 0.05
                CondBA  = abs(PBAEtaAux[ieta] - PBAEtaAux[jeta]) < 0.05
                CondEst = (EstEtaAux[ieta] == EstEtaAux[jeta])
                if not (CondAB and CondBA and CondEst):
                    jeta -= 1
                    break
            data.append([lname, ieta + 1, jeta + 1, PABEtaAux[ieta], PBAEtaAux[ieta], EstEtaAux[ieta]])
            ieta = jeta + 1

        aux   = pd.DataFrame(data, columns = ["LINEA", "INICIAL", "FINAL", "A-B", "B-A", "OPERATIVA"])
        aux   = aux.astype({"LINEA": str, "INICIAL": 'int32', "FINAL": 'int32', "A-B": 'float64', "B-A": 'float64', "OPERATIVA": bool})

        if df_manlin_show.empty:
            df_manlin_show = aux.copy()
        else:
            df_manlin_show = pd.concat([df_manlin_show, aux], ignore_index = True)
        
    # hay que generar la función "mock" en la que eventualmente el usuario modifica mant_lin_show
    def user_mod_mant(df_mantlin_ini: pd.DataFrame) -> pd.DataFrame:
        # aca se debe mandar la info del argumento a la interfaz de usuario y traer de vuelta 
        # la información eventualmente modificada

        # por ahora, no se hace nada.
        return df_mantlin_ini.copy()
    
    df_mantlin_fin = user_mod_mant(df_manlin_show)
    df_mantlin_fin.loc[~df_mantlin_fin['OPERATIVA'], ['A-B', 'B-A']] = 0.0, 0.0
    
    # preprocesamos el dataframe de modo de facilitar la escritura
    df_mantlin_fin["OP"] = df_mantlin_fin["OPERATIVA"].apply(lambda x: "T" if x else "F")
    
    mant_unique = df_mantlin_fin["LINEA"].unique()
    NLinMant = len(mant_unique)
    cols2    = ["INICIAL", "FINAL", "A-B", "B-A", "OP"]
    cols     = ["LINEA", "INICIAL", "FINAL", "A-B", "B-A", "OP"]

    df_full  = pd.DataFrame(columns = cols)
    mli_dict = {}

    # --- Preparar df_ml2 una sola vez ---
    ml2_ready = pd.DataFrame(columns=cols)
    if not df_ml2.empty:
        _ml2 = df_ml2.copy()
        _ml2.columns = cols
        _ml2["INICIAL"] = pd.to_numeric(_ml2["INICIAL"], errors='coerce')
        _ml2["FINAL"]   = pd.to_numeric(_ml2["FINAL"],   errors='coerce')
        _ml2["A-B"]     = pd.to_numeric(_ml2["A-B"],     errors='coerce')
        _ml2["B-A"]     = pd.to_numeric(_ml2["B-A"],     errors='coerce')
        _ml2["OP"]      = _ml2["OP"].apply(lambda x: "T" if x else "F")
        _ml2 = _ml2.dropna(subset=["INICIAL", "FINAL"])
        
        # Expandir los rangos de I:N en bloques unitarios (INICIAL=FINAL)
        ml2_expanded = []
        for _, row in _ml2.iterrows():
            ini = int(row["INICIAL"])
            fin = int(row["FINAL"])
            for b in range(ini, fin + 1):
                ml2_expanded.append([row["LINEA"], b, b, row["A-B"], row["B-A"], row["OP"]])
        
        if ml2_expanded:
            ml2_ready = pd.DataFrame(ml2_expanded, columns=cols)
            # EXTREMADAMENTE IMPORTANTE: I:N tiene rangos superpuestos. La macro los sobrescribe secuencialmente. 
            ml2_ready = ml2_ready.drop_duplicates(subset=["LINEA", "INICIAL"], keep='last')

    for i, row in df_mantlin_fin.iterrows():
        #print(lin)
        lin = row["LINEA"]
        ini = row["INICIAL"]
        fin = row["FINAL"]
        ab  = row["A-B"]
        ba  = row["B-A"]
        op  = row["OP"]

        INI = list(range(ini, fin +1))
        FIN = INI
        AB  = [ab for i in range(len(INI))]
        BA  = [ba for i in range(len(INI))]
        OP  = [op for i in range(len(INI))]
        LIN = [lin for i in range(len(INI))]

        data = {"LINEA": LIN, "INICIAL":INI, "FINAL": FIN, "A-B": AB, "B-A": BA, "OP": OP}
        df_aux = pd.DataFrame(columns = ["LINEA", "INICIAL", "FINAL", "A-B", "B-A", "OP"], data = data)

        if df_full.empty:
            df_full = df_aux.copy()
        else:
            df_full = pd.concat([df_full, df_aux], ignore_index=True)

    if not df_full.empty:
        df_full = df_full.dropna(subset=["INICIAL"])
        df_full["INICIAL"] = df_full["INICIAL"].astype('int32')
        df_full["FINAL"]   = df_full["FINAL"].astype('int32')
        df_full["FROM_AG"] = True

    # --- Construir dict de capacidades nominales desde la hoja Líneas ---
    nominal_cap = {}
    for _, row in df_lin.iterrows():
        lname = row["Nombre A->B"]
        nominal_cap[lname] = (float(row["A->B"]), float(row["B->A"]))

    # --- Integración A:G e I:N ANTES del filtro ---
    # I:N sobrescribe A:G completamente bloque a bloque.
    if df_full.empty:
        df_merged = ml2_ready.copy()
        if not df_merged.empty:
            df_merged["FROM_AG"] = False
    elif ml2_ready.empty:
        df_merged = df_full.copy()
    else:
        ag_subset = df_full[["LINEA", "INICIAL", "FROM_AG"]]
        df_merged = pd.concat([df_full, ml2_ready], ignore_index=True)
        # Mantener último (el valor de I:N gana)
        df_merged = df_merged.drop_duplicates(subset=["LINEA", "INICIAL"], keep='last')
        
        # Restaurar la flag FROM_AG para saber si el bloque existía en A:G
        df_merged = df_merged.drop(columns=["FROM_AG"], errors="ignore")
        df_merged = pd.merge(df_merged, ag_subset, on=["LINEA", "INICIAL"], how="left")
        df_merged["FROM_AG"] = df_merged["FROM_AG"].fillna(False)

    # --- Filtrar bloques finales ---
    TOLA = 0.05
    filtered_rows = []
    
    if not df_merged.empty:
        for lname in df_merged["LINEA"].unique():
            nom_ab, nom_ba = nominal_cap.get(lname, (None, None))
            grp = df_merged[df_merged["LINEA"] == lname].copy()
            if nom_ab is not None:
                # Regla de oro: Mantener si difiere de nominal, o es fallo, O estaba en A:G.
                # De esta forma, si I:N regresa un bloque de A:G a su valor nominal, 
                # SE IMPRIME con el valor nominal porque A:G lo había activado.
                mask = (
                    (abs(grp["A-B"].astype(float) - nom_ab) > TOLA) |
                    (abs(grp["B-A"].astype(float) - nom_ba) > TOLA) |
                    (grp["OP"] == "F") |
                    (grp["FROM_AG"] == True)
                )
                grp_filtered = grp[mask]
            else:
                grp_filtered = grp

            if not grp_filtered.empty:
                grp_filtered = grp_filtered.copy()
                grp_filtered["INICIAL"] = grp_filtered["INICIAL"].astype('int32')
                grp_filtered["FINAL"]   = grp_filtered["FINAL"].astype('int32')
                filtered_rows.append(grp_filtered)

    df_final = pd.concat(filtered_rows, ignore_index=True) if filtered_rows else pd.DataFrame()
    if not df_final.empty:
        df_final = df_final.sort_values(by=["LINEA", "INICIAL"]).reset_index(drop=True)

    # El conjunto de líneas es TODO el universo de líneas procesado (incluso con 0 bloques)
    mant_unique_final = list(df_merged["LINEA"].unique()) if not df_merged.empty else []
    
    # El orden del archivo de salida debe coincidir exactamente con el orden 
    # en que las líneas están definidas en la hoja "Líneas"
    nombres_lin = df_lin["Nombre A->B"].dropna().tolist()

    mant_unique_final = sorted(mant_unique_final, key=lambda x: nombres_lin.index(x) if x in nombres_lin else 9999)
    
    data_dict = {}
    mant_nblo = []
    
    for lin in mant_unique_final:
        if not df_final.empty and lin in df_final["LINEA"].values:
            grp = df_final[df_final["LINEA"] == lin]
            data_dict[lin] = grp[cols2].values
            mant_nblo.append(len(grp))
        else:
            data_dict[lin] = []
            mant_nblo.append(0)

    return data_dict, mant_unique_final, mant_nblo, len(mant_unique_final)


######## SIMULACIONES Y APERTURAS
def parse_simape(df_hid_xls: pd.DataFrame,    # hoja hirologia
                 df_eta_xls: pd.DataFrame,    # hoja etapas
                 df_cen_xls: pd.DataFrame,    # hoja centrales
                 sim_type  : TipoSimulacion,  # 'flag' de tipo simulacion
                 ale_type  : TipoAleatorio,   # 'flag' de tipo de aleatoriedad
                 si2_type  : TipoSimulacion2, # 'flag' de tipo de simluacion 2 (hist o aleat)
                 ULTIMOS_ANOS :bool  = True,
                 HIDRO_ESP : bool = False,
                 NO_APERT_FICT: bool = False
                ) -> tuple:
    
    df_eta = df_eta_xls.copy()
    df_eta = df_eta.dropna(subset=['Etapa', 'Nº Bloques'])
    df_eta = df_eta.astype({'Etapa': 'int64', 'Nº Días': 'int64', 'Año': 'int64', 'Nº Bloques': 'int64' })
    df_eta = df_eta[["Etapa", "Inicial", "Nº Días", "Final", "Año", "Mes", "Nº Bloques"]].copy()
    df_eta["Inicial"] = pd.to_datetime(df_eta["Inicial"])
    df_eta["Final"] = pd.to_datetime(df_eta["Final"])


    df_hid     = df_hid_xls.copy()


    NEtapas    = df_eta["Nº Bloques"].sum()
    NFil       = len(df_eta)
    FechaINI   = df_eta.loc[0, "Inicial"]
    NEta_Afl4s = 4
    Ano0       = FechaINI.year
    Mes0       = FechaINI.month
    NAno       = df_eta.loc[NFil - 1, "Inicial"].year - Ano0 + 1
    NSimul     = df_hid.iloc[0, 2]
    NApert     = NSimul
    NHidro     = df_hid.iloc[2, 2]
    MesDesh    = 7
    NHidro_Sec = df_hid.iloc[3, 2]
    NHidro_Med = df_hid.iloc[4, 2]
    NHidro_Hum = df_hid.iloc[5, 2]

    df_eta["IAno"]    = df_eta["Inicial"].dt.year - Ano0 + 1
    df_eta["IMes"]    = df_eta["Inicial"].dt.month
    df_eta["IMesAux"] = (df_eta["IMes"] + 9) % 12
    df_eta.loc[df_eta["IMesAux"] == 0, "IMesAux"] = 12

    df_eta["AnoCal"]  = df_eta["Inicial"].dt.year
    
    ArregloHidro = np.zeros(shape = (NSimul, NAno, NFil, NApert), dtype = int)
    logic = np.ones(NAno).astype(bool)
    
    if ale_type == TipoAleatorio.ALEATORIO_MES_SIM:
        for ISimul in range(NSimul):
            for IFil, row in df_eta.iterrows():
                IAno = row["IAno"]
                ArregloHidro[ISimul, IAno - 1, IFil, :] = ArregloNumAleat(NApert, NHidro, False)
    elif ale_type == TipoAleatorio.ALEATORIO_MES_CON:
        for IFil, row in df_eta.iterrows():
            IAno = row["IAno"]
            ArregloTMP = ArregloNumAleat(NApert, NHidro, False)
            for ISimul in range(NSimul):
                ArregloHidro[ISimul, IAno - 1, IFil, :] = ArregloTMP
    elif ale_type == TipoAleatorio.ALEATORIO_ANO_SIM:
        for ISimul in range(NSimul):
            for IFil, row in df_eta.iterrows():
                IAno = row["IAno"] - 1
                if logic[IAno]:
                    ArregloTMP = ArregloNumAleat(NApert, NHidro, False)
                    logic[IAno] = False
                ArregloHidro[ISimul, IAno, IFil, :] = ArregloTMP
    elif ale_type == TipoAleatorio.ALEATORIO_ANO_CON:
        for IFil, row in df_eta.iterrows():
            IAno = row["IAno"] - 1
            if logic[IAno]:
                if ULTIMOS_ANOS and NApert <= NSimul:
                #if True and NApert <= NSimul:
                    ArregloTMP = ArregloNumAleat(NApert, NHidro, False, IAno + 1, True)
                else:
                    ArregloTMP = ArregloNumAleat(NApert, NHidro, False)

                logic[IAno] = False
            for ISimul in range(NSimul):
                ArregloHidro[ISimul, IAno, IFil, :] = ArregloTMP
    else:
        raise ValueError("Error: Falta seleccionar dentro de Opciones de Aperturas")
        
    # de aca parte el codigo asociado a la subrutina Crea_Archivo_PLPIDSIM_ETA
    NEtapas = NFil # se cambia el valor de NEtapas

    # lo chequeos de consistencia de las dimensiones deben hacerse en el FRONTEND
    data = pd.DataFrame(index = np.arange(NFil), columns = ["mes", "etapa"] + ["s"+str(i) for i in range(1, NSimul + 1)])
    data["mes"]   = df_eta["IMesAux"].values
    data["etapa"] = df_eta["Etapa"].values

    ArregloSimul = np.zeros(shape = (NFil, NSimul), dtype = int)

    if si2_type == TipoSimulacion2.SIM_ALEATORIA:
        for irow, row in df_eta.iterrows():
            ArregloHidroSim = ArregloNumAleat(NSimul, NHidro, False)
            data.iloc[irow, 2:] = ArregloHidroSim 
            ArregloSimul[irow, :] = ArregloHidroSim 

    elif si2_type == TipoSimulacion2.SIM_HISTORICA:
        Flag_Aux    = False
        Flag_AnoCal = False
        IEtapa      = 0

        if sim_type == TipoSimulacion.PROGMENSUAL4s: 
            #print("FLAG_ANOCAL....")
            Flag_AnoCal = True

        #print(Flag_AnoCal)
        for irow, row in df_eta.iterrows():
            IAno    = row["IAno"]
            IMesAux = row["IMesAux"]
            Ano_Cal = row["AnoCal"]
            IMes    = row["IMes"]

            Mes00   = Mes0 + 11
            if Mes00 > 12: 
                Mes00 = Mes00 - 12
                Ano00 = Ano0 + 1
            else:
                Ano00 = Ano0
            
            #print(Ano0, Mes00, Ano_Cal, IMes)
            if datetime.datetime(Ano_Cal, IMes, 1) > datetime.datetime(Ano00, Mes00 , 1): Flag_AnoCal = False
            #print(Flag_AnoCal)
            if IAno != 1:
                if Flag_Aux:
                    if IMes < 4:
                        IAno_Aux = IAno - 1
                    else:
                        IAno_Aux = IAno
                else:
                    if IMes < 4:
                        IAno_Aux = IAno
                    else:
                        IAno_Aux = IAno + 1
            else:
                if Mes0 < 4:
                    if IMes < 4:
                        IAno_Aux = IAno
                    else:
                        IAno_Aux = IAno + 1
                else:
                    Flag_Aux = True
                    IAno_Aux = IAno


            BaseAux = 0
            #if ULTIMOS_ANOS: BaseAux = NHidro - NSimul
            if ULTIMOS_ANOS: BaseAux = NHidro - NSimul

            ArregloHidroSim = np.zeros(NSimul, dtype = int)

            for ISimul in range(1, NSimul - IAno_Aux + 2):
                IHid = ISimul + IAno_Aux - 1 + BaseAux
                ArregloHidroSim[ISimul - 1] = IHid

            IAux = np.maximum(NSimul - IAno_Aux + 1, 1)

            for ISimul in range(IAux, NSimul + 1):
                IHid = ISimul + IAno_Aux - 1 + BaseAux
                if IHid > NHidro:
                    ArregloHidroSim[ISimul - 1] = IAno_Aux - 1 + ISimul - NHidro + BaseAux
                else:
                    ArregloHidroSim[ISimul - 1] = IHid

            #print("Arreglo HIdro INI: ", ArregloHidroSim)
            if HIDRO_ESP:
                #print(irow,IAno_Aux, Flag_AnoCal)
                if IAno_Aux > 1 and Flag_AnoCal:
                    MHidro_Ord = pd.Series([NHidro_Sec, NHidro_Med, NHidro_Hum])
                    MHidro_Ord = MHidro_Ord.sort_values() # ordena de menor a mayor
                    ind_ord    = MHidro_Ord.index.to_list()
                    MHidro_Ord = MHidro_Ord.reset_index(drop = True)
                    MHidro_Ord = pd.concat([MHidro_Ord, pd.Series([0])], ignore_index = True)
                    #print("MHIDRO_ORD: ", MHidro_Ord)
                    
                    IAux_con = -1
                    for ISimul in range(1, NSimul + 1):
                        for IAux in range(1, 4):
                            #print("\tISImul, IAux: ", ISimul, IAux)
                            if (MHidro_Ord[IAux - 1] == ISimul):
                                ArregloHidroSim[ISimul - 1] = ISimul
                                #print("\t1- ArregloHidroSim[ISimul - 1] = ", ArregloHidroSim[ISimul - 1])
                                IAux_con = 1
                                if IAux < 3:
                                    #print("While...")
                                    #print("\tpos IAux + IAux_con - 1: ", IAux + IAux_con - 1, "Mhidro pos: ", MHidro_Ord[IAux + IAux_con - 1])
                                    #print("\t", MHidro_Ord)
                                    while ISimul + IAux_con == MHidro_Ord[IAux + IAux_con - 1] and IAux + IAux_con < 4:
                                        #print("\tpos IAux + IAux_con - 1: ", IAux + IAux_con - 1)
                                        IAux_con += 1
                                    #print("\tIAux_con: ", IAux_con)
                                if IAux > 1:
                                    if (ISimul - 1) != MHidro_Ord[IAux - 2]:
                                        if (NSimul == NHidro) and ISimul + IAux_con > NHidro:
                                            if MHidro_Ord[0] != 1:
                                                ArregloHidroSim[ISimul - 2] = 1 # menos 2 o menos 1?
                                            elif MHidro_Ord[1] != 2:
                                                ArregloHidroSim[ISimul - 2] = 2 # menos 2 o menos 1?
                                            else:
                                                ArregloHidroSim[ISimul - 2] = 2 # menos 2 o menos 1?
                                        else:
                                            ArregloHidroSim[ISimul - 2] = ISimul + IAux_con
                                else:
                                    if ISimul - 1 < 1:
                                        if MHidro_Ord[2] != NSimul and NSimul == NHidro:
                                            ArregloHidroSim[NSimul - 1] = ISimul + IAux_con
                                    else:
                                        if NSimul == NHidro and (ISimul + IAux_con > NHidro):
                                            ArregloHidroSim[ISimul - 2] = 1
                                        else:
                                            ArregloHidroSim[ISimul - 2] = ISimul + IAux_con
                                
                    
                # esto es codigo muestro, la planilla no permite modificar estos valores
            #    pass
            #print(ArregloHidroSim)
            data.iloc[irow, 2:] = ArregloHidroSim
            ArregloSimul[irow, :] = ArregloHidroSim

    # datos idsim
    txt_data_idsim = []
    for row in data.values:
        imes = row[0]
        ieta = row[1]
        line  = "{:>6s}".format("{:03d}".format(imes))
        line += "{:>6s}".format("{:03d}".format(ieta))
        for i in range(2, NSimul + 2):
            line += "{:>5s}".format("{:02d}".format(row[i]))
        txt_data_idsim.append(line)

    # aperturas    
    NApert_Fil = pd.Series(0, np.arange(NFil))
    NApert_Fil[:] = NApert

    ArregloHidroTemp = np.zeros(shape = (NSimul, 2, 4, NApert), dtype = int)
    if sim_type == TipoSimulacion.PROGMENSUAL4s:
        for ISimul in range(NSimul):
            for IFil in range(NEta_Afl4s):
                IAno = df_eta.loc[IFil, "IAno"]
                NApert_Fil[IFil] = 1
                ArregloHidroTemp[ISimul, IAno - 1, IFil, :] = ArregloHidro[ISimul, IAno - 1, IFil, :]
                ArregloHidro[ISimul, IAno - 1, IFil, :] = np.ones(NApert).astype(int)
                
    # preparación de datos
    df_eta["NApert"] = NApert_Fil
    sims = ["{:02d}".format(i) for i in range(1, NSimul + 1)]
    data_ape = {}

    for ISimul in range(NSimul):
        IEtapa = 0
        txt_data_ape = []
        for IFil, row in df_eta.iterrows():
            IAno    = row["IAno"]
            IMes    = row["IMes"]
            IMesAux = row["IMesAux"]
            napert  = row["NApert"]
            IEta    = row["Etapa"]
            line    = "{:>6s}".format("{:03d}".format(IMesAux))
            line   += "{:>6s}".format("{:03d}".format(IEta))
            line   += "{:>6s}".format("{:02d}".format(napert))
            if IMes < MesDesh + 3 and IMes > 3:
                for IApert in range(NApert_Fil[IFil]):
                    line += "{:>5s}".format("{:02d}".format(ArregloHidro[ISimul, IAno - 1, IFil, IApert]))
            else:
                for IApert in range(NApert_Fil[IFil]):
                    line += "{:>5s}".format("{:02d}".format(ArregloSimul[IFil, ISimul]))
            txt_data_ape.append(line)
        data_ape[sims[ISimul]] = txt_data_ape

    #dict_idape = {'idape': {"NSIMUL": NSimul, "NFIL": NFil, "DATA": data}}
    
    # aperturas 2
    MesIni = df_eta.loc[0,"IMes"]
    txt_data_ap2 = []
    for IFil, row in df_eta.iterrows():
        IAno    = row["IAno"]
        IMes    = row["IMes"]
        IMesAux = row["IMesAux"]
        napert  = row["NApert"]
        IEta    = row["Etapa"]

        if IFil == 0 : 
            IFil_Aux = IFil
        else:
            MesEtaAnt = df_eta.loc[IFil - 1, "IMes"]

        if IAno >= 2 and IMes <= 3:
            IAno_h = IAno - 1

            if IMes == 1 and IMes != MesEtaAnt :
                if sim_type == TipoSimulacion.PROGMENSUAL4s and IAno == 2:
                    if IFil + 1 >= 2 and IFil + 1 <= 5:
                        IFil_Aux = IFil
                        ArregloHidro[0, IAno_h - 1, 4, :] = ArregloHidroTemp[0, IAno_h - 1, IFil - 1, :]

                        if IFil + 1 <= 4:
                            IAno_h = IAno
                else:
                    IFil_Aux = IFil - 1
            elif IMes == 1 and IFil + 1 <= 5 and sim_type == TipoSimulacion.PROGMENSUAL4s:
                IFil_Aux = IFil

                if IFil <= 4:
                    IAno_h = IAno

        else:
            IAno_h = IAno
            IFil_Aux = IFil


        line    = "{:>6s}".format("{:03d}".format(IMesAux))
        line   += "{:>6s}".format("{:03d}".format(IEta))
        line   += "{:>6s}".format("{:02d}".format(napert))
        for IApert in range(NApert_Fil[IFil]):
            line += "{:>5s}".format("{:02d}".format(ArregloHidro[0, IAno_h - 1, IFil_Aux, IApert]))

        txt_data_ap2.append(line)
        
        # nfil, nsimul, idsim, idape, idap2
    return NFil, NSimul, txt_data_idsim, data_ape, txt_data_ap2

######### DEMANDA

# nueva función ene2025
def parse_demanda(df_barras_xls, df_demanda_xls):
    
    df_barras_xls    = df_barras_xls[~df_barras_xls.BARRA.isnull()]
    NDem             = df_barras_xls.shape[0]
    barras_list_full = df_barras_xls.BARRA.unique().tolist()
    barras_list_dem  = df_demanda_xls.BARRA.unique().tolist()
    barras_list_cero = [x for x in barras_list_full if x not in barras_list_dem]

    data1=df_demanda_xls[['Etapa', 'Mes', 'bloque_CEN','BARRA','MW']].drop_duplicates()
    data_dem=data1.rename(columns={"bloque_CEN":"Bloque"})

    data_dem['NBloque']=data_dem.Bloque.max() # esto habría que generalizarlo
    data_dem['Mes']=data_dem['Mes'].astype("int32")
    data_dem['Bloque']=data_dem['Bloque'].astype("int32")    
   
    data_values={x:list(map(list, data_dem[data_dem.BARRA==x][['Mes','Bloque','MW']].drop_duplicates().itertuples(index=False))) for x in data_dem.BARRA.unique()}    
    
    return NDem, data_dem[['BARRA','NBloque']].drop_duplicates(), data_values, barras_list_cero

######## MANTENIMIENTOS CENTRALES

def parse_mancen(df_dict : dict, POT_TOL = 0.05, macro_profile=None) -> pd.DataFrame:
    barradem    = df_dict["barrademf"].set_index("BARRA")
    df_barr_xls = df_dict['barras'].dropna(subset = "BARRA").astype({"Nº": 'int32'})
    df_etap_xls = df_dict["etapas"].dropna(subset = "Etapa")
    
    if macro_profile and macro_profile.skip_stages_offset > 0:
        offset = macro_profile.skip_stages_offset
        df_etap_xls = df_etap_xls.iloc[offset:].reset_index(drop=True)
        
    df_etap_xls = df_etap_xls.astype({"Etapa": "int32"})
    df_eta      = df_dict["etapas_full"]
    df_cent_xls = df_dict["centrales"]
    
    def _norm_mant(df):
        if df is None: return None
        res = df.copy()
        for col in res.columns:
            u_col = str(col).upper().replace('Í', 'I').replace('Á', 'A')
            if u_col == 'CENTRAL' or u_col == 'CENTRALES': res = res.rename(columns={col: 'central'})
            elif u_col == 'INICIAL' or u_col == 'FEC_INI' or 'INICIO' in u_col: res = res.rename(columns={col: 'INICIAL'})
            elif u_col == 'FINAL' or u_col == 'FEC_FIN' or 'FIN' in u_col: res = res.rename(columns={col: 'FINAL'})
            elif 'MINIMA' in u_col or 'P_MIN' in u_col: res = res.rename(columns={col: 'potmin'})
            elif 'MAXIMA' in u_col or 'P_MAX' in u_col or 'P_DISP' in u_col: res = res.rename(columns={col: 'potmax'})
        return res

    mcols_base = ["central", "INICIAL", "FINAL", "potmin", "potmax"]
    
    def _get_sheet_clean(name):
        df = _norm_mant(df_dict.get(name))
        if df is not None and not df.empty:
            df = df.dropna(subset=["central"])
            cols_avail = [c for c in mcols_base if c in df.columns]
            return df[cols_avail]
        return pd.DataFrame(columns=mcols_base)

    # Leer MantCEN (área derecha: columnas I-M con rangos de bloques ya procesados por VBA)
    # Esta hoja es la fuente única para plpmance.dat - contiene datos consolidados de todas las hojas de mantención
    raw_mcen = df_dict.get("MantCEN")
    if raw_mcen is not None and not raw_mcen.empty:
        # Columnas I-M (índices 8-12): CENTRAL, INICIAL(bloque), FINAL(bloque), MÍNIMA, MÁXIMA
        mcen_cols = raw_mcen.columns[8:13] if len(raw_mcen.columns) >= 13 else raw_mcen.columns[-5:]
        df_mcen_ranges = raw_mcen[list(mcen_cols)].copy()
        df_mcen_ranges.columns = ['central', 'blo_ini', 'blo_fin', 'potmin', 'potmax']
        df_mcen_ranges = df_mcen_ranges.dropna(subset=['central'])
        df_mcen_ranges = df_mcen_ranges[df_mcen_ranges['central'].astype(str).str.strip().str.match(r'^[A-Za-z_\-]')]
        df_mcen_ranges['central'] = df_mcen_ranges['central'].astype(str).str.strip()
        df_mcen_ranges['blo_ini'] = pd.to_numeric(df_mcen_ranges['blo_ini'], errors='coerce')
        df_mcen_ranges['blo_fin'] = pd.to_numeric(df_mcen_ranges['blo_fin'], errors='coerce')
        df_mcen_ranges = df_mcen_ranges.dropna(subset=['blo_ini', 'blo_fin'])
        df_mcen_ranges['blo_ini'] = df_mcen_ranges['blo_ini'].astype(int)
        df_mcen_ranges['blo_fin'] = df_mcen_ranges['blo_fin'].astype(int)
    else:
        df_mcen_ranges = pd.DataFrame(columns=['central', 'blo_ini', 'blo_fin', 'potmin', 'potmax'])

    aux_dem = pd.merge(barradem, df_barr_xls[["BARRA", "Nº"]].set_index("BARRA"), left_index = True, right_index = True).groupby(["Etapa", "BARRA","Nº", "fecha"]).agg({'MWh': 'sum'}).reset_index()
    Fallas, dfcentrales = get_centrales_dfs(df_eta, df_cent_xls, aux_dem, df_barr_xls)

    pivot = df_dict["blodem"][["Etapa","Mes", "fecha", "bloque_CEN"]].set_index("fecha")

    # Pre-calcular mes por bloque usando blodem (bloque_CEN 1-275 -> Mes)
    bloques_idx = range(1, 276)
    blodem_tmp = df_dict["blodem"][["bloque_CEN", "Mes"]].drop_duplicates("bloque_CEN")
    mes_val_dict = dict(zip(blodem_tmp["bloque_CEN"].astype(int), blodem_tmp["Mes"].astype(int)))

    # Procesar MantCEN: expandir rangos de bloques a filas individuales.
    # Todas las centrales (incluyendo ERNC) se leen desde MantCEN, que ya contiene
    # los datos consolidados y procesados por VBA con la estructura de pasadas correcta.
    # Cuando blo_ini retrocede respecto a la fila anterior de la misma central,
    # empieza una nueva "pasada"; cada pasada adicional se codifica con offset de 275
    # para mantener el orden al ordenar por bloque (el template luego aplica % 275).
    final_mants = []

    if not df_mcen_ranges.empty:
        prev_blo_ini_by_cen = {}
        pass_offset_by_cen  = {}
        for _, row in df_mcen_ranges.iterrows():
            cname   = str(row['central'])
            blo_ini = int(row['blo_ini'])
            blo_fin = int(row['blo_fin'])
            pmin_r  = float(row['potmin']) if pd.notna(row['potmin']) else 0.0
            pmax_r  = float(row['potmax']) if pd.notna(row['potmax']) else 0.0

            prev = prev_blo_ini_by_cen.get(cname, -1)
            if blo_ini <= prev:
                pass_offset_by_cen[cname] = pass_offset_by_cen.get(cname, 0) + 275
            prev_blo_ini_by_cen[cname] = blo_ini

            offset = pass_offset_by_cen.get(cname, 0)
            for b in range(blo_ini, blo_fin + 1):
                mes_v = mes_val_dict.get(((b - 1) % 275) + 1, 1)
                final_mants.append([cname, b + offset, mes_v, pmin_r, pmax_r])

    out = pd.DataFrame(columns=['central', 'bloque', 'Mes', 'potmin', 'potmax'], data=final_mants)
    df_mant = out.sort_values(by=["central", "bloque"]).reset_index(drop=True)
    
    # -------- FALLAS --------
    # Fallas tiene index horario, mapeamos a bloques via pivot y expandimos a 275 bloques
    try:
        falla_cols_lower = {str(c).lower().strip(): c for c in Fallas.columns}
        col_cen_f  = next((orig for k, orig in falla_cols_lower.items() if 'central' in k), None)
        col_pmin_f = next((orig for k, orig in falla_cols_lower.items() if 'potmin' in k), None)
        col_pmax_f = next((orig for k, orig in falla_cols_lower.items() if 'potmax' in k), None)
        col_fec_f  = next((orig for k, orig in falla_cols_lower.items() if 'fecha' in k), None)

        if col_cen_f is None or col_fec_f is None:
            raise ValueError(f"Columnas requeridas no encontradas en Fallas. Disponibles: {list(Fallas.columns)}")

        df_falla = Fallas[[col_fec_f, col_pmin_f, col_pmax_f, col_cen_f]].copy()
        df_falla.columns = ['fecha', 'potmin', 'potmax', 'central']

        # Unir con pivot para obtener bloque y Mes
        df_falla = df_falla.set_index('fecha').merge(pivot, how='left', left_index=True, right_index=True).reset_index()
        df_falla = df_falla.rename(columns={'bloque_CEN': 'bloque'})
        df_falla = df_falla.dropna(subset=['bloque'])
        df_falla['bloque'] = df_falla['bloque'].astype(int)

        # Agregar por central/bloque/Mes
        df_falla = df_falla.groupby(['central', 'bloque', 'Mes']).agg({'potmin': 'mean', 'potmax': 'mean'}).reset_index()

        # Expandir cada central de falla a los 275 bloques del horizonte
        if not df_falla.empty:
            falla_mants = []
            for cname_f in df_falla['central'].unique():
                df_f_cen = df_falla[df_falla['central'] == cname_f]
                blo_map_f = {int(r['bloque']): r for r in df_f_cen.to_dict('records')}
                for b in bloques_idx:
                    mes_v  = mes_val_dict[b]
                    pmin_f = float(blo_map_f[b]['potmin']) if b in blo_map_f else 0.0
                    pmax_f = float(blo_map_f[b]['potmax']) if b in blo_map_f else 0.0
                    falla_mants.append([cname_f, b, mes_v, pmin_f, pmax_f])
            df_falla = pd.DataFrame(falla_mants, columns=['central', 'bloque', 'Mes', 'potmin', 'potmax'])

        print(f"DEBUG: df_falla registros: {len(df_falla)}, centrales: {df_falla['central'].nunique() if not df_falla.empty else 0}")
    except Exception as e:
        print(f"ERROR en procesamiento de fallas: {e}. Columnas: {Fallas.columns.tolist()}")
        df_falla = pd.DataFrame(columns=["central", "bloque", "Mes", "potmin", "potmax"])

    print(f"DEBUG: df_mant total size: {len(df_mant)}")
    return df_mant[["central", "bloque", "Mes", "potmin", "potmax"]], df_falla[["central", "bloque", "Mes", "potmin", "potmax"]]
