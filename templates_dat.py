#achivo de templates como strings
#Etapas
ETA_TMPL =u'''# Archivo con la duracion de las etapas
# Etapas
{{"{:8d}".format(etapas.NETAPAS)}}   'H'
# Ano  Mes  Etapa FDesh   NHoras    FactTasa    TipoEtapa
{% for ano, mes, eta, fde, nho, fta, teta  in etapas.DATA -%}
{{"{:2s}".format(" ")}}{{"{:03d}".format(ano)}}  {{"{:03d}".format(mes)}}    {{"{:03d}".format(eta)}}     {{fde}}      {{"{:3d}".format(nho)}}    {{"{:.6f}".format(fta)}}    '{{teta}}'
{% endfor -%}
'''
#Bloques --> modificado abr2026 para igualar espacios en blanco
BLO_TMPL =u'''# Archivo con la duracion de los bloques
# Bloques
{{"{:>8d}".format(bloques.NBLO)}}
# Bloque   Etapa   NHoras  Ano   Mes  TipoBloque
{% for iblo, eta, horas, anio, mes , tipo  in bloques.DATA -%}
{{"{:>7s}".format("{:>03d}".format(iblo))}}{{"{:>7s}".format("{:03d}".format(eta))}}{{"{:>9s}".format("{:03.0f}".format(horas))}}{{"{:>7s}".format("{:03d}".format(anio))}}{{"{:>7s}".format("{:03d}".format(mes))}}    '{{"{:9s}".format(tipo)}}'
{% endfor -%}
'''
#Barras
BAR_TMPL =u'''# Archivo con definicion de Barras (plpbar.dat)
# Numero de Barras
     {{barras.NBARRAS}}
# Numero       Nombre
{% for item in barras.BNAMES -%}
{{"{}".format(loop.index).rjust(8)}}       '{{item}}'
{% endfor %}'''
#Lineas
#editado abr2026
LIN_TMPL =u'''# Archivo de configuracion de lineas (plpcnfli.dat)
# Num.Lineas   Modela Perdidas  Perd.en.ERM   Ang. de Ref.
{{"{:12d}".format(lineas.NLINEAS)}}{{"{:>11s}".format(lineas.MODPRED)}}             '{{lineas.PERDERM}}'{{"{:>16}".format(lineas.REFANG)}}
# Caracteristicas de las Lineas
# Nombre                                              F.Max. A-B F.Max. B-A  Barra A  Barra B   Tension  R(Ohm)  X(ohm)   Mod.Perd.  Num.Tramos   Operativa
{% for name, fab, fba, ba, bb, v, r, x, p, nt, o  in lineas.DATA -%}
{{"{:<48s}".format("'"+name+"'")}}{{"{:>10.1f}".format(fab)}}{{"{:>11.1f}".format(fba)}}{{"{:>9.0f}".format(ba)}}{{"{:>9.0f}".format(bb)}}{{"{:>10.1f}".format(v)}}{{"{:>8.3f}".format(r)}}{{"{:>8.3f}".format(x)}}{{"{:>7s}".format(p)}}{{"{:>12.0f}".format(nt)}}{{"{:>13s}".format(o)}}
{% endfor %}
'''
#Extracciones
EXT_TMPL =u'''# Archivo de Extracciones (plpextrac.dat)
# Numero Centrales con extraccion   
{{extracciones.NCEN}}
{% for central, valor, central2 in extracciones.DATA -%}
# Nombre de central de extraccion    
'{{central}}'                         
# Maxima Extraccion (m3/seg)         
{{valor}}
# Nombre de la Central aguas abajo   
'{{central2}}'
{% endfor -%}

'''
#Rendimientos
REN_TMPL =u'''# Archivo de Rendimiento de Embalses (plpcenre.dat)
# Numero de Embalses con Rendimiento  
{{rendimientos.NEMB}}
{% for name, rendmed, vol, pend, const, fesc, numcen, rend  in rendimientos.DATA -%}
# Nombre de Central
'{{name}}'
# Nombre del Embalse
'{{name}}'
# Rendimiento Medio
{{rendmed}}
# Numero de Tramos
1
#Tramo      Volumen     Pendiente    Constante  F.Escala
     1    {{"{:8f}".format(vol)}}{{"{:14.8f}".format(pend)}}{{"{:13.8f}".format(const)}}{{"{:9.1E}".format(fesc).replace('+','')}}
{% endfor -%}

'''
#Filtraciones
FIL_TMPL =u'''# Archivo de Filtraciones de Embalses (plpfiln.dat)
# Numero Embalses con filtraciones  
{{filtraciones.NEMB}}
{% for name, central2, filtmed, ntram, numcen, numcenFin  in filtraciones.fixed -%}
# Nombre de embalse                  
'{{name}}'     
# Filtraciones medias                
{{filtmed}}         
# Numero de Tramos                   
{{ntram}}
#Tramo    Vol[10e6 m3]	Pendiente	Constante
{% for tramo, vol, pend, const, const_mod  in filtraciones.DATA[name] -%}
{{"{:>6.0f}".format(tramo)}}     {{"{:<9.1f}".format(vol)}}{{"{:15.9f}".format(pend)}}{{"{:15.9f}".format(const)}}
{% endfor -%}
# Nombre de la Central aguas abajo   
'{{central2}}'
{% endfor %}
'''

#Rebalses
REB_TMPL =u'''# Archivo de Volumenes de vertimiento de Embalses (plpvrebemb.dat)
# Numero Embalses con volumenes espe
{{rebalses.NEMB}}
{% for name, volreb, costo  in rebalses.DATA -%}
# Nombre del Embalse
'{{name}}'
# Volumen de Rebalse [ 10^3 m3 ]
{{volreb}}
# Costo de Rebalse                   
{{costo}}
{% endfor %}
'''

#CENPMAX
PMX_TMPL =u'''# Archivo con cuva pmax en funcion del volumen
# Numero de embalses  
{{cenpmax.NEMB}}
{% for name, emb, ntram in cenpmax.fixed -%}
# Nombre de Central                  
'{{name}}'     
# Nombre Embalse                
'{{emb}}'         
# Numero de Segmentos                   
{{ntram}}
# Volumen [10e6 m3]			Pendiente		Coeficiente
{% for vol, pend, const  in cenpmax.DATA[name] -%}
{{"{:<9.1f}".format(vol)}}{{"{:15.9f}".format(pend)}}{{"{:15.9f}".format(const)}}
{% endfor -%}
{% endfor -%}
'''

#Laja (ojo aca hay un tema con los ultimos 2 sets de datos)
# editado mar2026
LAJ_TMPL =u'''# Archivo con la definicion del nuevo convenio de riego Laja 
# Nombre Central Lago Laja
{{"{:<32s}".format("'"+laja.CenNomLaja+"'")}}
# Numero Caudales Hoya Intermedia
{{"{:<15}".format(laja.NumQHoInt)}}
# Nombre Caudales Hoya Intermedia
{% for cname  in laja.NomQHoInt -%}
{{"{:<32s}".format("'"+cname+"'")}}
{% endfor -%}
# Volumen maximo Lago Laja
{{"{:<15.1f}".format(laja.VolMaxLaja)}}
# Numero de colchones
{{"{:<15}".format(laja.NumCol)}}
# Volumen util colchones
{% for vol  in laja.VolUtCol -%}
{{"{:.1f}\t".format(vol)}}
{%- endfor %}
# Derecho base y factores  incrementales de derechos de riego por colchon
{% for fact  in laja.DeBaFactIncRieCol -%}
{{"{:.2f}\t".format(fact)}}
{%- endfor %}
# Derecho base y factores  incrementales de derechos electricos por colchon
{% for fact  in laja.DeBaFactIncEleCol -%}
{{"{:.2f}\t".format(fact)}}
{%- endfor %}
# Derecho base y factores  incrementales de derechos mixtos por colchon
{% for fact  in laja.DeBaFactIncMixCol -%}
{{"{:.2f}\t".format(fact)}}
{%- endfor %}
# Derecho maximo (riego, electrico, mixto y anticipos)
{% for demax  in laja.DeMax -%}
{{"{:.0f}\t".format(demax)}}
{%- endfor %}
# Mes inicio temporada de riego y anticipos (1/12 y 1/9), en meses hidrologicos
{% for imes  in laja.MesIniRieg -%}
{{"{:<5d}".format(imes)}}
{%- endfor %}
# Caudal Maximo [m3/s] derechos riego, electrico, mixtos y anticipados
{% for qmax  in laja.QMaxDeRieg -%}
{{"{:<5.0f}".format(qmax)}}
{%- endfor %}
# Costos de riego no servido y uso derechos riego, electrico, mixtos y anticipos
{% for cori  in laja.CoRiegNoSer -%}
{{"{:<7.1f}".format(cori)}}
{%- endfor %}
# Factor mensual de costo de riego no servido ano hidrologico abr-mar
{% for fact  in laja.FactMesRiegNoSer -%}
{{"{:<6.1f}".format(fact)}}
{%- endfor %}
# Factor mensual de costo de derechos de riego ano hidrologico abr-mar
{% for fact  in laja.FactMesCoDeRiegAnoHid -%}
{{"{:<6.1f}".format(fact)}}
{%- endfor %}
# Factor mensual de costo de derechos electricos ano hidrologico abr-mar
{% for fact  in laja.FactMesCoDeElecAnoHid -%}
{{"{:<6.1f}".format(fact)}}
{%- endfor %}
# Factor mensual de costo de derechos mixto ano hidrologico abr-mar
{% for fact  in laja.FactMesCoDeMixAnoHid -%}
{{"{:<6.1f}".format(fact)}}
{%- endfor %}
# Factor mensual de costo de gasto anticipado ano hidrologico abr-mar
{% for fact  in laja.FactMesCoGaAntAnoHid -%}
{{"{:<6.1f}".format(fact)}}
{%- endfor %}
# Factor máximo de uso mensual de derechos de riego ano hidrologico abr-mar
{% for fact  in laja.FactMaxUsoMesDeRiegAnoHid -%}
{{"{:<6.2f}".format(fact)}}
{%- endfor %}
# Factor máximo de uso mensual de derechos electricos ano hidrologico abr-mar
{% for fact  in laja.FactMaxUsoMesDeElecAnoHid -%}
{{"{:<6.2f}".format(fact)}}
{%- endfor %}
# Factor máximo de uso mensual de derechos mixtos ano hidrologico abr-mar
{% for fact  in laja.FactMaxUsoMesDeMixAnoHid -%}
{{"{:<6.2f}".format(fact)}}
{%- endfor %}
# Factor máximo de uso mensual de derechos anticipados ano hidrologico abr-mar
{% for fact  in laja.FactMaxUsoMesDeAntAnoHid -%}
{{"{:<6.2f}".format(fact)}}
{%- endfor %}
# Derechos iniciales disponibles para riego, elect, mixto y anticipos
{% for deini  in laja.DeIniDispRieg -%}
{{"{:<6.0f}".format(deini)}}
{%- endfor %}
# Numero de retiros de riego
{{"{:<3}".format(laja.NumRetRieg)}}
# Nombre Retiro Zanartu-Collao
{{"{:<32s}".format("'"+laja.NomRetZaCo+"'")}}
# Nombre inyeccion retiro ZaCo
{{"{:<32s}".format("'"+laja.NomInyZaCo+"'")}}
# Factor Costo, Porcentajes de retiro 1oReg, 2oReg, Emer, Saltos en Zanartu-Collao
{% for fact  in laja.FactZaCo -%}
{{"{:<15.3f}".format(fact)}}
{%- endfor %}
# Nombre Retiro Tucapel
{{"{:<32s}".format("'"+laja.NomRetTuc+"'")}}
# Nombre inyeccion retiro Tucapel
{{"{:<32s}".format("'"+laja.NomInyRetTuc+"'")}}
# Factor Costo, Porcentajes de retiro 1oReg, 2oReg, Emer, Saltos en Tucapel
{% for fact  in laja.FactTuc -%}
{{"{:<15.3f}".format(fact)}}
{%- endfor %}
# Nombre Retiro Saltos
{{"{:<32s}".format("'"+laja.NomRetSalt+"'")}}
# Nombre inyeccion retiro Saltos
{{"{:<32s}".format("'"+laja.NomInyRetSalt+"'")}}
# Factor Costo, Porcentajes de retiro 1oReg, 2oReg, Emer, Saltos en Saltos del Laja
{% for fact  in laja.FactSalt -%}
{{"{:<15.3f}".format(fact)}}
{%- endfor %}
# Filtraciones históricas
{{laja.FiltHist}}
# Caudales de demanda de riego por defecto por regantes
{% for qdem  in laja.QDemRiegDefReg -%}
{{"{:<15.1f}".format(qdem)}}
{%- endfor %}
# Curva variación estacional primeros regantes por defecto mensual ano hidrologico abr-mar
{% for cvar  in laja.CurVarEstAnoHid1Reg -%}
{{"{:<6.2f}".format(cvar)}}
{%- endfor %}
# Curva variación estacional segundos regantes por defecto mensual ano hidrologico abr-mar
{% for cvar  in laja.CurVarEstAnoHid2Reg -%}
{{"{:<6.2f}".format(cvar)}}
{%- endfor %}
# Curva variación estacional primeros regantes EMERGENCIAS por defecto mensual ano hidrologico abr-mar
{% for cvar  in laja.CurVarEstAnoHidEme -%}
{{"{:<6.2f}".format(cvar)}}
{%- endfor %}
# Curva variación estacional Saltos del Laja por defecto mensual ano hidrologico abr-mar
{% for cvar  in laja.CurVarEstAnoHidSaltLaja -%}
{{"{:<6.2f}".format(cvar)}}
{%- endfor %}
# Volumen muerto
{{"{:<15.1f}".format(laja.VolMuerto)}}
# Retiro manuales de riego por etapa por retiro (m3/s)
# Etapas
{{"{:0.0f}".format(laja.RetManRiegEtaRet)}}
# Etapa   1oReg     2oReg     Emer      Saltos
{% if laja.RetManRiegEtaRet > 0 %}
{{"{:0.0f}".format(laja.QRet[0])}}    {{"{:.1f}".format(laja.QRet[1])}}    {{"{:.1f}".format(laja.QRet[2])}}    {{"{:.1f}".format(laja.QRet[3])}}    {{"{:.1f}".format(laja.QRet[4])}}
{%- endif -%}
# Caudales forzados en El Toro por etapa (m3/s)
# Etapas
{{laja.NumEtaQForz}}
# NEtapa  QGxElToro
{% if laja.NumEtaQForz > 0 -%}
1         {{"{:.2f}      ".format(laja.QForzToro)}}
{% endif %}
'''
#Maule 
#editado mar2026
MAU_TMPL =u'''# Archivo de convenio del Maule (plpmaule.dat)
# Nombre Central Embalse Maule    
{{"{:<30s}".format("'"+maule.CenNomMaule+"'")}}
# Nombre Central Laguna Invernada 
{{"{:<30s}".format("'"+maule.CenNomLagInv+"'")}}
# Nombre Central Embalse Melado   
{{"{:<30s}".format("'"+maule.CenNomEmbMel+"'")}}
# Nombre Central Embalse Colbun   
{{"{:<30s}".format("'"+maule.CenNomEmbColb+"'")}}
# Numero Caudales Hoya Intermedia 
{{"{:<15.0f}".format(maule.NumQHoyInt)}}
# Nombre Caudales Hoya Intermedia 
{% for nom  in maule.NomQHoyInt -%}
{{"{:<20s}".format("'"+nom+"'")}}
{% endfor -%}          
# VEmbalseUtilMin (en 10^3 m3)    
{{"{:<15.0f}".format(maule.VEmbalseUtilMin)}}
# VReservaExtraord (en 10^3 m3)   
{{"{:<15.0f}".format(maule.VReservaExtraord)}}
# VReservaOrdinaria (en 10^3 m3)  
{{"{:<15.0f}".format(maule.VReservaOrdinaria)}}
# VDerRiegoTempMax (en 10^3 m3)   
{{"{:<15.0f}".format(maule.VDerRiegoTempMax)}}
# VDerElectAnuMax (en 10^3 m3)    
{{"{:<15.0f}".format(maule.VDerElectAnuMax)}}
# VCompElecMax (en 10^3 m3)       
{{"{:<15.0f}".format(maule.VCompElecMax)}}
# VGastoElecMenIni (en 10^3 m3)   
{{"{:<15.0f}".format(maule.VGastoElecMenIni)}}
# VGastoElecAnuIni (en 10^3 m3)   
{{"{:<15.0f}".format(maule.VGastoElecAnuIni)}}
# VGastoRiegoIni (en 10^3 m3)     
{{"{:<15.0f}".format(maule.VGastoRiegoIni)}}
# VGastoRExtElecIni (en 10^3 m3)  
{{"{:<15.0f}".format(maule.VGastoRExtElecIni)}}
# VGastoRExtRiegoIni (en 10^3 m3) 
{{"{:<15.0f}".format(maule.VGastoRExtRiegoIni)}}
# VDerRExtElecIni (en 10^3 m3)    
{{"{:<15.1f}".format(maule.VGastoRExtRiegoIni)}}
# VDerRExtRiegoIni (en 10^3 m3)   
{{"{:<15.1f}".format(maule.VDerRExtRiegoIni)}}
# VCompElecIni (en 10^3 m3)       
{{"{:<15.1f}".format(maule.VCompElecIni)}}
# VEconInverIni (en 10^3 m3)      
{{"{:<15.1f}".format(maule.VEconInverIni)}}
# GastoElecMenMax (en m3/seg)     
{{"{:<15.0f}".format(maule.GastoElecMenMax)}}
# GastoElecDiaMax (en m3/seg)     
{{"{:<15.0f}".format(maule.GastoElecDiaMax)}}
# Modulacion porcentual de GastoElecDiaMax mensual en reserva (%)               
{% for mod  in maule.ModPorcMen -%}
{{"{:.0f} ".format(mod)}} 
{%- endfor %}
# Descuenta caudales de derechos electricos del balance en Armerillo            
{{"{:<9}".format(maule.DescQDeArm)}}
# Gasto Riego Maximo [m3/seg]     
{{"{:<15.0f}".format(maule.GaRiegMax)}}
# Caudal Maule Minimo para embalsa
{% for item in maule.QMauMinEmb -%}{{"{:<4s}".format(item|round|int|string if item is number else item|string)}}{% endfor %}
# Valor Riego servido Conv Maule & Res 105                                      
{% for rieg in maule.ValRiegSer105 -%}{{"{0:.0f} ".format(rieg)}}{% endfor %}    
# Costo Riego no servido Conv Maule & Res 105                                   
{% for costo in maule.CoRiegNoSer105 -%}{{"{0:.0f} ".format(costo)}}{% endfor %}    
# Porcentaje de riego mensuales Maule (segun mes en plpeta.dat)                 
{% for por in maule.PorRiegMenMau -%}{{"{0:.0f} ".format(por)}}{% endfor %}
# Agnos iniciales de porcentajes de riego mensuales Maule manuales              
{{"{:<15.0f}".format(maule.AnoIniPorcRiegMenMau)}}
# Porcentajes de riego mensuales Maule manuales (segun mes en plpeta.dat)       
{% for por in maule.PorRiegMenMauMan -%}{{"{0:.0f} ".format(por)}}{% endfor %}
# Ano desde donde se aplica modulacion automatica de caudal riego de Maule en reserva (0 -> desactiv
{{"{:<15.0f}".format(maule.AnoModAutQRiegMau)}}
# Factor de caudales futuros en disponibilidad de riego                                             
{{"{:<15.1f}".format(maule.FactQFutDispRieg)}}
# Modulacion automatica afecta tambien a la Res 105                             
{{"{:<9}".format(maule.ModAutoRes105)}}
# Volumen acumulado de derechos de riego para terminar la temporada [10^3 m3]   
{% for vol in maule.VolAcDeRieg -%}
{% if loop.index == 1 -%}
{{"{:<8.0f}".format(vol)}}
{%- else -%}
{{"{0:.0f} ".format(vol)}}
{%- endif %}
{%- endfor %}
# Dias acumulados para terminar la temporada de riego                           
{% for nd in maule.DiAcTemp -%}
{{"{:.0f} ".format(nd)}}
{%- endfor %}
# Porcentaje Caudal de derechos entrantes electricos en Reserva Maule           
{{"{:<15.0f}".format(maule.PorQDeEntElec)}}
# Porcentaje Caudal de derechos entrantes riego en Reserva Maule                
{{"{:<15.0f}".format(maule.PorQDeEntRiegMau)}}
# Caudales de riego mensuales Res 105 (segun mes en plpeta.dat)                 
{% for q in maule.QRiegMen105 -%}
{{"{:.0f} ".format(q)}}
{%- endfor %}
# Agnos iniciales de porcentajes de riego mensuales Caud Res 105 manuales       
{{"{:<15.0f}".format(maule.AnoIniPorRiegMenQ105Man)}}
# Caud Res 105 de riego mensuales manuales (segun mes en plpeta.dat)            
{% for q in maule.QRes105RiegMenMan -%}
{{"{:.0f} ".format(q)}}
{%- endfor %}
# Numero de retiros de riego      
{{"{:<15.0f}".format(maule.NumRetRieg)}}
# Nombres de centrales de retiro                                                
{% for nom in maule.NomCenRet -%}
{{"{:<30s}".format("'"+nom+"'")}}
{% endfor -%}            
# Porcentajes de retiro                                                         
{% for por in maule.PorRet -%}
{{"{:s} ".format(por)}} 
{%- endfor %}     
# Holgura en retiro de riego                                                    
{% for hol in maule.HolRetRieg -%}
{{"{0:} ".format(hol)}}
{%- endfor %}
# Bocatoma Canelon                
{{"{:<15s}".format("'"+maule.BocCan+"'")}}
# Costo Obra Civil Canelon, por m3/seg  
{{"{:<15.0f}".format(maule.CoObrCivCan)}}
# Indice de la Extraccion de Colbun con cota disp. 425 
{{"{:<15.0f}".format(maule.IndExtrColbCot425)}}
# Volumen Cota Disponibildad 425 (10^3 m3)  
{{"{:<15.0f}".format(maule.VolCotDisp425)}}
# Economías Invernada: uso en Reserva Ordinaria, son acumulables, Costo Almacenamiento              
{% for item in maule.EcInv -%}{{"{0:} ".format(item)}}{% endfor %}
# Costo regla no embalsar Invernada, Costo regla mantener cota                                      
{% for item in maule.CoRegNoEmbInv -%}{% if loop.first %}{{"{0:.0f}  ".format(item)}}{% else %}{{"{0:.0f} ".format(item)}}{% endif %}{% endfor %}

'''

#Centrales
#editado mar2026
CEN_TMPL=u'''# Archivo de configuracion de las centrales (plpcnfce.dat)
# Num.Centrales  Num.Embalses Num.Serie Num.Fallas Num.Pas.Pur. Num.BAT
{{"{:9}".format(centrales.NCEN)}}{{"{:14}".format(centrales.NEMB)}}{{"{:13d}".format(centrales.NSER)}}{{"{:10d}".format(centrales.NFALLA)}}{{"{:11d}".format(centrales.NPAS)}}{{"{:11d}".format(centrales.NBAT)}}
# Interm Min.Tec. Cos.Arr.Det. FFaseSinMT EtapaCambioFase
  F      F        F            F          00
# Caracteristicas Centrales
# Centrales de Embalse
{% for numcen,central,cvar, rend,nbar,ggen,gvert,fcf,afl1ersem, indhid, volini,volfin,volmin,volmax,potmin,potmax,vertmin,vertmax, fesc  in centrales.EMBALSES -%}
{{"{:<49s}".format(' ')}} IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep  Cen_NEtaArr Cen_NEtaDet
{{"{:>5d} ".format(numcen)}}'{{"{:<s}".format(central)}}'{{"{:{width}}".format(" ", width = 48-(central|length))}}1    F       F       F       F{{"{:>12s}".format(indhid)}}          0           0
{{"{:<10s}".format(' ')}}PotMin PotMax VertMin VertMax
{{"{:>16s}".format("{:06.1f}".format(potmin) if potmin < 0 else "{:05.1f}".format(potmin))}}{{"{:>7s}".format("{:05.1f}".format(potmax))}}{{"{:>8s}".format("{:05.1f}".format(vertmin))}}{{"{:>8s}".format("{:05.1f}".format(vertmax))}}
           Start   Stop ON(t<0) NEta_OnOff
             0.0    0.0 F       0               Pot.           Volumen    Volumen    Volumen    Volumen  Factor
          CosVar  Rendi  Barra Genera Vertim    t<0  Afluen    Inicial      Final     Minimo     Maximo  Escala EmbCFUE
{{"{:>16.1f}".format(cvar)}}{{"{:>7.3f}".format(rend)}}{{"{:>7d}".format(nbar)}}{{"{:>7d}".format(ggen)}}{{"{:>7d}".format(gvert)}}    0.0  {{"{:06.1f}".format(afl1ersem)}}{{"{:>11.7f}".format(volini)}}{{"{:>11.7f}".format(volfin)}}{{"{:>11.7f}".format(volmin)}}{{"{:>11.7f}  ".format(volmax)}}{{"{:<7s}".format(fesc)}}{{"{:>7s}".format(fcf)}}
{% endfor -%}
# Centrales Serie Hidraulica
{% for numcen,central,cvar,rend,nbar,ggen,gvert,fcf,afl1ersem,indhid,potmin,potmax,vertmin,vertmax in centrales.SERIES -%}
{{"{:<49s}".format(' ')}} IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep  Cen_NEtaArr Cen_NEtaDet
{{"{:>5d} ".format(numcen)}}'{{"{:<s}".format(central)}}'{{"{:{width}}".format(" ", width = 48-(central|length))}}1    F       F       F       F{{"{:>12s}".format(indhid)}}          0           0
{{"{:<10s}".format(' ')}}PotMin PotMax VertMin VertMax
{{"{:>16s}".format("{:06.1f}".format(potmin) if potmin < 0 else "{:05.1f}".format(potmin))}}{{"{:>7s}".format("{:05.1f}".format(potmax))}}{{"{:>8s}".format("{:05.1f}".format(vertmin))}}{{"{:>8s}".format("{:05.1f}".format(vertmax))}}
           Start   Stop ON(t<0) NEta_OnOff
             0.0    0.0 F       0               Pot.
          CosVar  Rendi  Barra SerHid SerVer    t<0  Afluen
{{"{:>16.1f}".format(cvar)}}{{"{:>7.3f}".format(rend)}}{{"{:>7d}".format(nbar)}}{{"{:>7d}".format(ggen)}}{{"{:>7d}".format(gvert)}}    0.0  {{"{:06.1f}".format(afl1ersem)}}
{% endfor -%}
# Centrales Pasada Puras
{% for numcen,central,cvar,rend,nbar,ggen,gvert,fcf,afl1ersem,indhid,potmin,potmax,vertmin,vertmax in centrales.PASADAS -%}
{{"{:<49s}".format(' ')}} IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep  Cen_NEtaArr Cen_NEtaDet
{{"{:>5d} ".format(numcen)}}'{{"{:<s}".format(central)}}'{{"{:{width}}".format(" ", width = 48-(central|length))}}1    F       F       F       F{{"{:>12s}".format(indhid)}}          0           0
{{"{:<10s}".format(' ')}}PotMin PotMax VertMin VertMax
{{"{:>16s}".format("{:06.1f}".format(potmin) if potmin < 0 else "{:05.1f}".format(potmin))}}{{"{:>7s}".format("{:05.1f}".format(potmax))}}{{"{:>8s}".format("{:05.1f}".format(vertmin))}}{{"{:>8s}".format("{:05.1f}".format(vertmax))}}
           Start   Stop ON(t<0) NEta_OnOff
             0.0    0.0 F       0               Pot.
          CosVar  Rendi  Barra SerHid SerVer    t<0  Afluen
{{"{:>16.1f}".format(cvar)}}{{"{:>7.3f}".format(rend)}}{{"{:>7d}".format(nbar)}}{{"{:>7d}".format(ggen)}}{{"{:>7d}".format(gvert)}}    0.0  {{"{:06.1f}".format(afl1ersem)}}
{% endfor -%}
# Centrales Termicas o Embalses Equivalentes,FV, EO, CS
{% for numcen,central,cvar,rend,nbar,ggen,gvert,fcf,afl1ersem,indhid,potmin,potmax,vertmin,vertmax in centrales.TERMICAS -%}
{{"{:<49s}".format(' ')}} IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep  Cen_NEtaArr Cen_NEtaDet
{{"{:>5d} ".format(numcen)}}'{{"{:<s}".format(central)}}'{{"{:{width}}".format(" ", width = 48-(central|length))}}1    F       F       F       F{{"{:>12s}".format(indhid)}}          0           0
{{"{:<10s}".format(' ')}}PotMin PotMax VertMin VertMax
{{"{:>16s}".format("{:06.1f}".format(potmin) if potmin < 0 else "{:05.1f}".format(potmin))}}{{"{:>7s}".format("{:05.1f}".format(potmax))}}{{"{:>8s}".format("{:05.1f}".format(vertmin))}}{{"{:>8s}".format("{:05.1f}".format(vertmax))}}
           Start   Stop ON(t<0) NEta_OnOff
             0.0    0.0 F       0               Pot.
          CosVar  Rendi  Barra SerHid SerVer    t<0  Afluen
{{"{:>16.1f}".format(cvar)}}{{"{:>7.3f}".format(rend)}}{{"{:>7d}".format(nbar)}}{{"{:>7d}".format(ggen)}}{{"{:>7d}".format(gvert)}}    0.0  {{"{:06.1f}".format(afl1ersem)}}
{% endfor -%}
# Baterias y Fallas
{% for numcen,central,cvar,rend,nbar,ggen,gvert,fcf,afl1ersem,indhid,potmin,potmax,vertmin,vertmax in centrales.BATERIAS -%}
{{"{:<49s}".format(' ')}} IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep  Cen_NEtaArr Cen_NEtaDet
{{"{:>5d} ".format(numcen)}}'{{"{:<s}".format(central)}}'{{"{:{width}}".format(" ", width = 48-(central|length))}}1    F       F       F       F{{"{:>12s}".format(indhid)}}          0           0
{{"{:<10s}".format(' ')}}PotMin PotMax VertMin VertMax
{{"{:>16s}".format("{:06.1f}".format(potmin) if potmin < 0 else "{:05.1f}".format(potmin))}}{{"{:>7s}".format("{:05.1f}".format(potmax))}}{{"{:>8s}".format("{:05.1f}".format(vertmin))}}{{"{:>8s}".format("{:05.1f}".format(vertmax))}}
           Start   Stop ON(t<0) NEta_OnOff
             0.0    0.0 F       0               Pot.
          CosVar  Rendi  Barra SerHid SerVer    t<0  Afluen
{{"{:>16.1f}".format(cvar)}}{{"{:>7.3f}".format(rend)}}{{"{:>7d}".format(nbar)}}{{"{:>7d}".format(ggen)}}{{"{:>7d}".format(gvert)}}    0.0  {{"{:06.1f}".format(afl1ersem)}}
{% endfor -%}
{% for numcen,central,cvar,rend,nbar,ggen,gvert,fcf,afl1ersem,indhid,potmin,potmax,vertmin,vertmax in centrales.FALLAS -%}
{{"{:<49s}".format(' ')}} IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep  Cen_NEtaArr Cen_NEtaDet
{{"{:>5d} ".format(numcen)}}'{{"{:<s}".format(central)}}'{{"{:{width}}".format(" ", width = 48-(central|length))}}1    F       F       F       F{{"{:>12s}".format(indhid)}}          0           0
{{"{:<10s}".format(' ')}}PotMin PotMax VertMin VertMax
{{"{:>16s}".format("{:06.1f}".format(potmin) if potmin < 0 else "{:05.1f}".format(potmin))}}{{"{:>7s}".format("{:05.1f}".format(potmax))}}{{"{:>8s}".format("{:05.1f}".format(vertmin))}}{{"{:>8s}".format("{:05.1f}".format(vertmax))}}
           Start   Stop ON(t<0) NEta_OnOff
             0.0    0.0 F       0               Pot.
          CosVar  Rendi  Barra SerHid SerVer    t<0  Afluen
{{"{:>16.1f}".format(cvar)}}{{"{:>7.3f}".format(rend)}}{{"{:>7d}".format(nbar)}}{{"{:>7d}".format(ggen)}}{{"{:>7d}".format(gvert)}}    0.0  {{"{:06.1f}".format(afl1ersem)}}
{% endfor -%}
'''

#Afluentes
AFL_TMPL =u'''# Archivo de caudales por etapa
# Nro. Cent. c/Caudales Estoc. (EstocNVar2) y Nro. Hidrologias (NClase)
{{"{:>5d}".format(aflce.NCAU)}}                                         {{aflce.NHIDRO}}
{% for cname  in aflce.NOMCAU -%}
# Nombre de la central
'{{cname}}'
#   Numero de bloques con caudales
{{"{:03d}".format(aflce.NETA)}}
# Mes   Bloque    Caudal
{% for line in aflce.QETA[cname] -%}
{{line}}
{% endfor -%}
{% endfor %}
'''

#Costos centrales
# editado may2026
COS_TMPL = u'''# Archivo de precios de termicas (plpcosce.dat)
# Numero de centrales termicas con cambio de costo variable
 {{cosce.IMANT}} 
{% for cname, neta in cosce.DATA -%}
# Nombre de la central
'{{cname}}'
# Numero de etapas
{{"{:>6}".format("{:02d}".format(neta))}}
# Mes   Etapa    CosVar
{% for ieta in range(cosce.NFIL) -%}
{% if cosce.MANTCEN[cname][ieta] == 1 -%}
{% set imes = cosce.IMES[ieta] -%}
{% set cv   = cosce.CVARETA[cname][ieta] -%}
{% set num_eta = cosce.ETAPAS[ieta] -%}
{{"{:>5}".format("{:02d}".format(imes))}}{{"{:>8}".format("{:03d}".format(num_eta))}}{{"{:>10}".format("{:05.1f}".format(cv))}}
{% endif -%}
{% endfor -%}
{% endfor -%}
'''

#Mantenimientos embalses
EMB_TMPL = u'''# Archivo de mantenimientos embalses (plpmanem.dat)
# Numero de embalses con mantenimientos
 {{mantemb.NEMB}} 
{% for ename in  mantemb.DATA -%}
# Nombre del embalse
'{{ename}}'
#   Numero de Etapas con mantenimiento
{{"{:>6d}".format(mantemb.DATA[ename].NMANT)}}
#   Mes   Etapa     VolMin     VolMax
{% for ieta, imes, vmin, vmax in mantemb.DATA[ename].DATA -%}
{{"{:>7s}".format("{:>02.0f}".format(imes))}}{{"{:>8s}".format("{:>03.0f}".format(ieta))}}{{"{:>11s}".format("{:>8.7f}".format(vmin))}}{{"{:>11s}".format("{:>8.7f}".format(vmax))}}
{% endfor -%}
{% endfor -%}
'''

#Mantenimientos embalses H
#editado may2026
EMH_TMPL = u'''# Archivo de minimos de embalses con holgura (plpminembh.dat)
# Numero de embalses con mantenimientos
{{"{:>2s}".format("{:2d}".format(manemh|length))}} 
{% for ename in manemh -%}
# Nombre del embalse
'{{ename}}'
#   Numero de Etapas con vmin
{{"{:>6s}".format("{:02d}".format(manemh[ename].NMANT))}}
# Etapa     VolMin     Costo
{% for ieta, vmin, costo in manemh[ename].DATA -%}
{{"{:>8s}".format("{:03.0f}".format(ieta))}}{{"{:>11s}".format("{:8.7f}".format(vmin))}}{{"{:>11s}".format("{:6.4f}".format(costo))}}
{% endfor -%}
{% endfor -%}
'''

#Mantenimientos lineas
#editado mar2026
MLI_TMPL = u'''# Archivo de mantenimientos de lineas (plpmanli.dat)
# numero de lineas con matenimientos
 {{mantlin.NMANT}} 
{% for lname, nblo in mantlin.LINEAS -%}
# Nombre de la lineas
'{{lname}}'
#   Numero de Bloques con mantenimiento
{{"{:>6}".format("{:02d}".format(nblo))}}
#   NumeroBloque PotMaxAB   PotMaxBA     Operativa
{% for ini, fin, ab, ba, op in mantlin.DATA[lname]-%}
{{"{:>6}".format("{:03d}".format(ini))}}{{"{:>18}".format("{:2.1f}".format(ab))}}{{"{:>11}".format("{:2.1f}".format(ba))}}{{"{:>10}".format(op)}}
{% endfor -%}
{% endfor %}
'''

#indice de simulaciones
SIM_TMPL =u'''# Archivo de caudales por etapa
# Numero de simulaciones y etapas con caudales
{{"{:>8s}".format("{:>02d}".format(idsim.NSIMUL))}}{{"{:>8s}".format("{:>02d}".format(idsim.NFIL))}}
# Mes   Etapa  SimulInd(1,...,NSimul)
{% for row in idsim.DATA-%}
{{row}}
{% endfor -%}
'''

#indice de aperturas
APE_TMPL =u'''# Archivo de caudales por etapa
# Numero de simulaciones y etapas con caudales
{{"{:>8s}".format("{:>02d}".format(idape.NSIMUL))}}{{"{:>8s}".format("{:>02d}".format(idape.NFIL))}}
{% for idsim in idape.DATA -%}
# Mes   Etapa  NApert ApertInd(1,...,NApert) - Simulacion={{idsim}}
{% for row in idape.DATA[idsim]-%}
{{row}}
{% endfor -%}
{% endfor -%}
'''

#indice de aperturas 2
AP2_TMPL =u'''# Archivo de caudales por etapa (plpidap2.dat)
# Numero de etapas con caudales
{{"{:>8s}".format("{:>02d}".format(idape2.NFIL))}}
# Mes   Etapa  NApert ApertInd(1,...,NApert)
{% for row in idape2.DATA -%}
{{row}}
{% endfor -%}
'''

#Baterias
BAT_TMPL =u'''#Archivo de caracteristicas de baterias (plpcenbat.dat)
# Numero de baterias total, Numero maximo de inyecciones
{{cenbat.NBAT}}          {{cenbat.MAXINJ}}
# Baterias
{% for idx, name, barra, rend_desc, cap_min, cap_max, cen_carga, rend_carga in cenbat.DATA -%}
{{idx}}     {{name}}
     # Numero de centrales que inyectan
          1
     # Central que inyecta, Factor de perdida de carga
     {{cen_carga}}     {{"{:.2f}".format(rend_carga)}}
# Barra, Factor de perdida de carga, Capacidad minima, Capacidad maxima
{{barra}}     {{"{:.2f}".format(rend_desc)}}     {{"{:.1f}".format(cap_min)}}     {{"{:.1f}".format(cap_max)}}
{% endfor -%}
'''

#PLEM --> pedido por JAP
PLEM1_TMPL=u'''#Numero, Nombre, Tipo, Barra, N/A, VolMin, VolMax, VolMinNECF, VolMaxNECF, FEscala, FactRendim
{% for numero, nombre, tipo, barra, na, volmin, volmax, volminnecf, volmaxnecf, fescala, factrendim in plem1.DATA -%}
{{"{:2s}".format(numero)}}, {{nombre}}, {{tipo}},  {{"{:3s}".format(barra)}},  {{na}}, {{volmin}}, {{volmax}}, {{volminnecf}}, {{volmaxnecf}}, {{fescala}}, {{factrendim}}
{% endfor %}
'''

#DEMANDA --> cortesia de JAP --> modificado abr2026
DEM_TMPL=u'''# Archivo de demandas por barra (plpdem.dat)
# Numero de barras
{{demanda.NDem}}
{% for cname, neta in demanda.DATA1 -%}
# Nombre de la Barra
'{{cname}}'
# Numero de Demandas
{{neta}}
# Mes  Etapa   Demanda
{% for Mes, Bloque, MW in demanda.DATA2[cname] -%}
{{'{:>5s}'.format('{:>02d}'.format(Mes))}}{{'{:>7s}'.format('{:>03d}'.format(Bloque))}}{{'{:10.2f}'.format(MW)}}
{% endfor -%}
{% endfor -%}
{% for barra in demanda.DATA3 -%}
# Nombre de la Barra
'{{barra}}'
# Numero de Demandas
 0 
{% endfor -%}
'''

#MANTENIMIENTOS CENTRALES
#modificado mar2026
MANT_TMPL = u'''# Archivo de mantenimientos de centrales (plpmance.dat)
# numero de centrales con matenimientos
 {{mantcen.NTOT + mantcen_falla.NTOT}} 
{% for cenname in mantcen.CEN -%}
# Nombre de la central
'{{cenname}}'
#   Numero de Bloques e Intervalos
{{"{:>6s}".format("{:02.0f}".format(mantcen["DATA"][cenname]["NMANT"]))}}                 01
#   Mes    Bloque  NIntPot   PotMin   PotMax
{% for mes, blo, pmin, pmax in  mantcen["DATA"][cenname]["DATA"] -%}
{{"{:>7s}".format("{:02.0f}".format(mes))}}{{"{:>9s}".format("{:03.0f}".format(blo))}}        1{{"{:>9.2f}".format(pmin)}}{{"{:>9.2f}".format(pmax)}}
{% endfor -%}
{% endfor -%}
{% for cenname in mantcen_falla.CEN -%}
# Nombre de la central
'{{cenname}}'
#   Numero de Etapas e Intervalos
{{"{:>6s}".format("{:02.0f}".format(mantcen_falla.DATA[cenname]["NMANT"]))}}                 01
#   Mes    Etapa  NIntPot   PotMin   PotMax
{% if mantcen_falla.DATA[cenname].SUM > 0.0 -%}
{% for mes, blo, pmin, pmax in  mantcen_falla["DATA"][cenname]["DATA"] -%}
{{"{:>5s}".format("{:02.0f}".format(mes))}}{{"{:>9s}".format("{:03.0f}".format(blo))}}        1{{"{:>9.1f}".format(pmin)}}{{"{:>9.2f}".format(pmax)}}
{% endfor -%}
{% else -%}
{% for mes, blo, pmin, pmax in  mantcen_falla["DATA"][cenname]["DATA"] -%}
{{"{:>5s}".format("{:02.0f}".format(mes))}}{{"{:>9s}".format("{:03.0f}".format(blo))}}        1{{"{:>9.1f}".format(pmin)}}{{"{:>9.1f}".format(pmax)}}
{% endfor -%}
{% endif -%}
{% endfor -%}


'''

