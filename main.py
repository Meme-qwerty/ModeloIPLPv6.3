import argparse
from os import getcwd, path
from utils import *
from main_functions import parse_from_excel_to_dict, dicts_to_dfs, write_dat_files

def main(caseIPLP):

    case=path.join(getcwd(),  caseIPLP)
    
    # mar2026: blodur y nbloques se determinan dinámicamente desde el Excel
    #        : el usuario define Nº Bloques (3, 5 o 10) en la hoja Etapas del Excel
    
    opts_dict={'SIM0':TipoSimulacion.NOCONDICIONADA4s,
            'APE0':TipoAleatorio.ALEATORIO_ANO_CON,
            'AUX0':TipoSimulacion2.SIM_HISTORICA, 
            'UANO':True, 
            'HIDE':False,
            'NAPEF':False, 
            'CDEC':False, 
            'AFL4':False,
              }

    print("parse Excel")
    json_in=parse_from_excel_to_dict(case)

    print("json2dataframe")
    df_dict=dicts_to_dfs(json_in)

    print("start write dat")
    out_dir = path.join(getcwd(), "ArchivosDat")
    write_dat_files(df_dict, out_dir, opts_dict)

if __name__=='__main__':

    parser = argparse.ArgumentParser(description='Parse Excel IPLP y escritura archivos dat')
    parser.add_argument('--casoIPLP', nargs='?', required=True)
    args = parser.parse_args()
    caso=args.casoIPLP

    main(caso)
