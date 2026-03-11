# archivo con contenedores auxiliares (laja y maule)
TAGS_LAJA = [('CenNomLaja', None, str), 
             ('NumQHoInt', None, int), 
             ('NomQHoInt', list, str), 
             ('VolMaxLaja', None, float),
             ('NumCol', None, int), 
             ('VolUtCol', list, float), 
             ('DeBaFactIncRieCol', list, float), 
             ('DeBaFactIncEleCol', list, float),
             ('DeBaFactIncMixCol', list, float), 
             ('DeMax', list, float), 
             ('MesIniRieg', list, int), 
             ('QMaxDeRieg', list, float), 
             ('CoRiegNoSer', list, float), 
             ('FactMesRiegNoSer', list, float),
             ('FactMesCoDeRiegAnoHid', list, float), 
             ('FactMesCoDeElecAnoHid', list, float), 
             ('FactMesCoDeMixAnoHid', list, float), 
             ('FactMesCoGaAntAnoHid', list, float),
             ('FactMaxUsoMesDeRiegAnoHid', list, float), 
             ('FactMaxUsoMesDeElecAnoHid', list, float),
             ('FactMaxUsoMesDeMixAnoHid', list, float), 
             ('FactMaxUsoMesDeAntAnoHid', list, float), 
             ('DeIniDispRieg', list, float), 
             ('NumRetRieg', None, int), 
             ('NomRetZaCo', None, str), 
             ('NomInyZaCo', None, str), 
             ('FactZaCo',list, float), 
             ('NomRetTuc', None, str), 
             ('NomInyRetTuc', None, str), 
             ('FactTuc', list, float), 
             ('NomRetSalt', None, str), 
             ('NomInyRetSalt', None, str), 
             ('FactSalt', list, float), 
             ('FiltHist', None, float),
             ('QDemRiegDefReg', list, float), 
             ('CurVarEstAnoHid1Reg', list, float), 
             ('CurVarEstAnoHid2Reg', list, float), 
             ('CurVarEstAnoHidEme', list, float), 
             ('CurVarEstAnoHidSaltLaja', list, float), 
             ('VolMuerto', None, float),
             (None, None, None), 
             ('RetManRiegEtaRet', None, float),
             (None, None, None), 
             ('QRet', list, float), 
             (None, None, None),  
             ('NumEtaQForz', None, int),
             (None, None, None), 
             ('QForzToro', None, float)]

TAGS_MAULE = [('CenNomMaule', None, str), 
              ('CenNomLagInv', None, str), 
              ('CenNomEmbMel', None, str), 
              ('CenNomEmbColb', None, str),
              ('NumQHoyInt', None, int), 
              ('NomQHoyInt', list, str), 
              ('VEmbalseUtilMin', None, float), 
              ('VReservaExtraord', None, float),
              ('VReservaOrdinaria', None, float), 
              ('VDerRiegoTempMax', None, float), 
              ('VDerElectAnuMax', None, float), 
              ('VCompElecMax', None, float), 
              ('VGastoElecMenIni', None, float), 
              ('VGastoElecAnuIni', None, float),
              ('VGastoRiegoIni', None, float), 
              ('VGastoRExtElecIni', None, float), 
              ('VGastoRExtRiegoIni', None, float), 
              ('VDerRExtElecIni', None, float),
              ('VDerRExtRiegoIni', None, float), 
              ('VCompElecIni', None, float),
              ('VEconInverIni', None, float), 
              ('GastoElecMenMax', None, float), 
              ('GastoElecDiaMax', None, float), 
              ('ModPorcMen', list, float), 
              ('DescQDeArm', None, str), 
              ('GaRiegMax', None, float), 
              ('QMauMinEmb',list, [float, str]), 
              ('ValRiegSer105', list, float), 
              ('CoRiegNoSer105', list, float), 
              ('PorRiegMenMau', list, float), 
              ('AnoIniPorcRiegMenMau', None, int), 
              ('PorRiegMenMauMan', list, float), 
              ('AnoModAutQRiegMau', None, int), 
              ('FactQFutDispRieg', None, float),
              ('ModAutoRes105', None, str),
              ('VolAcDeRieg', list, float),
              ('DiAcTemp', list, float),
              ('PorQDeEntElec', None, float),
              ('PorQDeEntRiegMau', None, float), 
              ('QRiegMen105', list, float), 
              ('AnoIniPorRiegMenQ105Man', None, int), 
              ('QRes105RiegMenMan', list, float), 
              ('NumRetRieg', None, int),
              ('NomCenRet', list, str), 
              ('PorRet', list, float),
              ('HolRetRieg', list, str), 
              ('BocCan', None, str), 
              ('CoObrCivCan', None, float),  
              ('IndExtrColbCot425', None, int),
              ('VolCotDisp425', None, float), 
              ('EcInv', list, [str, str, 0.1]),
              ('CoRegNoEmbInv', None, float)]

# diccionario de cambio de nombres df_centrales
CHG_COL_NAME ={'INDICE':'numcen', 'CENTRALES':'central','Tipo de Central':'tipo',
                 'Rendimiento [MWh/m3s]':'rendimiento', 'Conectada a la Barra':'barra','Generación':'ggen',
                 'Vertimiento':'gvert', 'Función Costo Futuro':'fcf','Afluente Estocástico':'aflest',
                 'Estadística Semanal':'estsem', 'Afluente Primera Semana':'afl1ersem','Independencia Hidrológica':'indhid',
                 'Pronóstico de Deshielo':'prondesh', 'Volumen Mínimo hm3':'volmindesh','Volumen Máximo hm3':'volmaxdesh',
                 'Mes del Pronóstico':'mespron', 'Pronóstico Asociado':'pronasoc','Inicial':'cotainicial',
                 'Final':'cotafinal', 'Mínima':'cotamin','Máxima':'cotamax',
                 'Inicial.1':'volini', 'Final.1':'volfin','Mínimo':'volmin','Máximo':'volmax',
                 'Mínima.1':'potmin', 'Máxima.1':'potmax','Mínimo.1':'vertmin','Máximo.1':'vertmax',
                 'Costo Variable':'cvariable',}

# nombres de columnas de dataframes

CEN_COLS = ['INDICE', 'CENTRALES', 'Tipo de Central', 'Costo Variable',
       'Rendimiento [MWh/m3s]', 'Conectada a la Barra', 'Generación',
       'Vertimiento', 'Función Costo Futuro', 'Afluente Estocástico',
       'Estadística Semanal', 'Afluente Primera Semana',
       'Independencia Hidrológica', 'Pronóstico de Deshielo',
       'Volumen Mínimo hm3', 'Volumen Máximo hm3', 'Mes del Pronóstico',
       'Pronóstico Asociado', 'Inicial', 'Final', 'Mínima', 'Máxima',
       'Inicial.1', 'Final.1', 'Mínimo', 'Máximo', 'Mínima.1', 'Máxima.1',
       'Mínimo.1', 'Máximo.1', 'Afluente Primera Semana.1',
       'Afluente Segunda Semana', 'Afluente Tercera Semana',
       'Afluente Cuarta Semana', 'Unnamed: 34', 'Volumen Mínimo 2S hm3',
       'Volumen Máximo 2S hm3', 'Pronóstico SPC Asociado',
       'Potencia minima (Empuntamiento)', 'Potencia maxima (Empuntamiento)',
       'Capacidad de regulacion MWh', 'Potencia Bruta Máxima',
       'Consumos Propios', 'TSF', 'Factor TSFE']

# nombres columnas dataframe de centrales

NAMES_DICT_CEN = {'INDICE':'numcen', 'CENTRALES':'central','Tipo de Central':'tipo',
                 'Rendimiento [MWh/m3s]':'rendimiento', 'Conectada a la Barra':'barra','Generación':'ggen',
                 'Vertimiento':'gvert', 'Función Costo Futuro':'fcf','Afluente Estocástico':'aflest',
                 'Estadística Semanal':'estsem', 'Afluente Primera Semana':'afl1ersem','Independencia Hidrológica':'indhid',
                 'Pronóstico de Deshielo':'prondesh', 'Volumen Mínimo hm3':'volmindesh','Volumen Máximo hm3':'volmaxdesh',
                 'Mes del Pronóstico':'mespron', 'Pronóstico Asociado':'pronasoc','Inicial':'cotainicial',
                 'Final':'cotafinal', 'Mínima':'cotamin','Máxima':'cotamax',
                 'Inicial.1':'volini', 'Final.1':'volfin','Mínimo':'volmin','Máximo':'volmax',
                 'Mínima.1':'potmin', 'Máxima.1':'potmax','Mínimo.1':'vertmin','Máximo.1':'vertmax',
                 'Costo Variable':'cvariable',}

# diccionario auxiliar de str mes a imes HIDRO

HIMONTH = { 'Ene': 10, 
            'Feb': 11, 
            'Mar': 12, 
            'Abr': 1, 
            'May': 2,
            'Jun': 3,
            'Jul': 4,
            'Ago': 5,
            'Sep': 6,
            'Oct': 7,
            'Nov': 8,
            'Dic': 9
}

IMONTH = { 'Ene': 1, 
            'Feb': 2, 
            'Mar': 3, 
            'Abr': 4, 
            'May': 5,
            'Jun': 6,
            'Jul': 7,
            'Ago': 8,
            'Sep': 9,
            'Oct': 10,
            'Nov': 11,
            'Dic': 12
}

##### Diccionario de parseo de excel

EXCEL_DICT = {"etapas":{"sheet_name":"Etapas", "header":3,"usecols":"A:Q"},
          "consumo":{"sheet_name":"Consumo", "header":3,"usecols":"A:I"},
          "demandaR0":{"sheet_name":"Demanda-R", "header":5,"usecols":"A:AX"},
          "demandaL0":{"sheet_name":"Demanda-L", "header":5,"usecols":"A:AX"},
          "demandaLD0":{"sheet_name":"Demanda-LD", "header":5,"usecols":"A:AX"},
           "CaudalesAh1": {"sheet_name": "Caudales_Ah1", "header": 4, "usecols": "A:BE"},
           "CaudalesAh2": {"sheet_name": "Caudales_Ah2", "header": 4, "usecols": "A:BE"},
            "Historicos" : {"sheet_name": "Caudales_historicos", "header": 4, "usecols": "A:BE"},
          #"UC":{"sheet_name":"UC", "header":0,"usecols":"A:L"},
          "Hidrologia":{"sheet_name":"Hidrología", "header":0,"usecols":"B:D"},
          "barras":{"sheet_name":"Barras", "header":4,"usecols":"A:B"},        
          "lineas":{"sheet_name":"Líneas", "header":4,"usecols":"A:N"},
          "centrales":{"sheet_name":"Centrales", "header":4,"usecols":"A:AS"},
          "cvariable":{"sheet_name":"CV_MP", "header":4,"usecols":"A:E"},
          "manLin":{"sheet_name":"MantLIN", "header":4,"usecols":"A:G"},
          "manLin2":{"sheet_name":"MantLIN", "header":4,"usecols":"Q:V"},
          "CIniciales":{"sheet_name":"C.Iniciales(1)", "header":4,"usecols":"B:F"},
          "DispComb":{"sheet_name":"Disp.Combust.(2)", "header":4,"usecols":"B:F"},
          "Limitaciones":{"sheet_name":"Limitaciones(3)", "header":4,"usecols":"B:F"},
          "MMayor":{"sheet_name":"Mant.Mayor(4)", "header":4,"usecols":"B:F"},
          "PObra":{"sheet_name":"Plan de Obras(5)", "header":4,"usecols":"B:F"},
          "ERNC":{"sheet_name":"ERNC(6)", "header":4,"usecols":"A:F"},
          "MantEMB":{"sheet_name":"MantEMB", "header":4,"usecols":"A:F"},
          "MantEMBh":{"sheet_name":"MantEMBh", "header":4,"usecols":"B:F"},
          "MAULEN":{"sheet_name":"MAULEN", "header":3, "usecols":"C:Q"},
          "LAJAM":{"sheet_name":"LAJAM", "header":3,"usecols":"C:Q"},
          "Rebalse":{"sheet_name":"Rebalse", "header":0,"usecols":"A:C"},                            # opcional
          "Extracciones":{"sheet_name":"Extracciones", "header":0,"usecols":"A:C"},                  # opcional
          "Filtraciones":{"sheet_name":"Filtraciones", "header":0,"usecols":"A:H"},                  # opcional
          "Rendimientos":{"sheet_name":"Rendimiento", "header":0,"usecols":"A:F"},                   # opcional
          "CenPmax":{"sheet_name":"CENPMAX", "header":0,"usecols":"A:G"},                            # agregado, opcional
          "flags":{"sheet_name":"Datos", "header":None,"usecols":"Q:R"},                              # agregado
          "feriados": {"sheet_name": "Consumo", "header": 3, "usecols": "K:K"},                     # agregado ene2025
          "Baterias": {"sheet_name": "Baterias", "header": 5, "usecols": "A:K"}}                    # agregado mar2026


###### diccionario de mapeo archivo .dat ->( nombre de funcion generadora de diccionario, template, lista de dependencias de dataframes

'''
DAT_FUNC = { 'plpeta.dat'     :  ('get_etapas_dict', ETA_TMPL, ["etapas"]),
              #'plpblo.dat'    :  ('get_bloques_dict',BLO_TMPL),
              'plpbar.dat'    :  ('get_barras_dict', BAR_TMPL, ["barras"]),
              'plpcnfli.dat'  :  ('get_lineas_dict', LIN_TMPL, ["lineas"]),
              'plpextrac.dat' :  ('get_extrac_dict', EXT_TMPL, ["Extracciones"]),
              'plpcenre.dat'  :  ('get_cerend_dict', REN_TMPL, ["Rendimientos", "centrales"]),
              'plpvrebemb.dat':  ('get_rebemb_dict', REB_TMPL, ["Rebalse"]),
              'plpfilemb.dat' :  ('get_filemb_dict', FIL_TMPL, ["Filtraciones", "centrales"]),
              'plpcenpmax.dat':  ('get_cepmax_dict', PMX_TMPL, ["CenPmax"]),
              'plplajam.dat'  :  ('get_lajam_dict', LAJ_TMPL, ["LAJAM"]),
              'plpmaulen.dat' :  ('get_maulen_dict', MAU_TMPL, ["MAULEN"]),
              'plpcnfce.dat'  :  ('get_cnfcen_dict', CEN_TMPL, ["centrales"]),
              'plpidsim.dat' :   ('get_simape_dict', SIM_TMPL, ["Hidrologia", "etapas", "centrales"]),
              'plpidape.dat' :   ('get_simape_dict', APE_TMPL, ["Hidrologia", "etapas", "centrales"]),
              'plpidap2.dat' :   ('get_simape_dict', AP2_TMPL, ["Hidrologia", "etapas", "centrales"]),
              'plpmanem.dat' :   ('get_manem_dict', EMB_TMPL, ["MantEMB", "etapas", "centrales"]),
              'plpmanemh.dat':   ('get_manemh_dict', EMH_TMPL, ["MantEMBh", "etapas", "centrales"]),
              'plpmanli.dat' :   ('get_manli_dict' , MLI_TMPL, ["lineas", "manLin", "etapas", "centrales"]),
              'plpcosce.dat' :   ('get_cosce_dict' , COS_TMPL, ["cvariable", "etapas", "centrales"]),
              'plpaflce.dat' :   ('get_aflce_dict' , AFL_TMPL, ["Hidrologia", "CaudalesAh1", "CaudalesAh2", "Historicos", "etapas", "centrales", "flag"]),
              'plpdem.dat'   :   ('get_demanda_dict' , DEM_TMPL, ["barradem","blodem", "barras"]),
              'plpmancen.dat':   ('get_demanda_dict', MANT_TMPL, ["barrademf", "etapas_full", "barras", "centrales", 
                                                                  "CIniciales", "PObra", "Limitaciones", "DispComb", "MMayor", "ERNC"])
}
'''

##### mapeo mes calendario mes hidrológico y viceversa por índices -> nov2024
MES_MESC = {4:1,5:2,6:3,7:4,8:5,9:6,10:7,11:8, 12:9, 1:10, 2:11, 3:12}

MESC_MES = {10:1, 11:2, 12:3, 1:4, 2:5, 3:6, 4:7, 5:8, 6:9, 7:10, 8:11, 9:12}

##### configuraciones predefinidas de bloques -> mar2026
# mapea cantidad de bloques a distribucion de horas (deben sumar 24)
BLOQUES_CONFIG = {
    3:  [8, 8, 8],
    5:  [6, 3, 8, 3, 4],
    10: [3, 2, 3, 2, 2, 3, 2, 3, 2, 2],
}
