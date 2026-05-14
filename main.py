import argparse
import os
from os import getcwd, path
from utils import *
from main_functions import parse_from_excel_to_dict, dicts_to_dfs, write_dat_files
from macro_profiles import MACRO_REGISTRY, get_profile

def select_excel():
    files = [f for f in os.listdir(getcwd()) if f.endswith(('.xlsm', '.xlsx', '.xlsb'))]
    if not files:
        print("No se encontraron archivos Excel en esta carpeta.")
        return None
    print("\nSeleccionar Excel:")
    for i, f in enumerate(files, 1):
        print(f"[{i}] {f}")
    choice = input("Elegir numero: ").strip()
    idx = int(choice) - 1 if choice.isdigit() else 0
    return files[idx] if 0 <= idx < len(files) else files[0]

def select_macro():
    profiles = list(MACRO_REGISTRY.values())
    print("\nSeleccionar Macro")
    for i, p in enumerate(profiles, 1):
        print(f"[{i}] {p.display_name} ({p.name})")
    choice = input("Elegir numero: ").strip()
    idx = int(choice) - 1 if choice.isdigit() else 0
    return profiles[idx] if 0 <= idx < len(profiles) else profiles[0]

def main(caseIPLP, macro_profile=None, filter_files=None):
    case = path.join(getcwd(), caseIPLP)
    if macro_profile is None:
        macro_profile = get_profile('MacroPLP_I_20250508')

    opts_dict = {'SIM0': TipoSimulacion.NOCONDICIONADA4s,
                 'APE0': TipoAleatorio.ALEATORIO_ANO_CON,
                 'AUX0': TipoSimulacion2.SIM_HISTORICA, 
                 'UANO': True, 
                 'HIDE': False,
                 'NAPEF': False, 
                 'CDEC': False, 
                 'AFL4': False,
                 'macro_profile': macro_profile # Inyectamos el perfil
                }

    print(f"\nINICIANDO GENERACION: {caseIPLP} ")
    print(f"USANDO PERFIL: {macro_profile.display_name} \n")

    json_in = parse_from_excel_to_dict(case)

    df_dict = dicts_to_dfs(json_in)

    out_dir = path.join(getcwd(), "ArchivosDat")
    write_dat_files(df_dict, out_dir, opts_dict, filter_files=filter_files)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse Excel IPLP y escritura archivos dat')
    parser.add_argument('--casoIPLP', help='Nombre del archivo Excel')
    parser.add_argument('--macro', help='Nombre de la macro a emular (opcional)')
    parser.add_argument('--files', nargs='+', help='Lista de archivos .dat a generar (ej: plplajam.dat plpeta.dat)')
    args = parser.parse_args()

    caso = args.casoIPLP
    macro_name = args.macro

    if not caso:
        caso = select_excel()
    
    if not caso:
        exit()
    profile = None
    
    if macro_name:
        profile = MACRO_REGISTRY.get(macro_name)

    if not profile:
        profile = MACRO_REGISTRY.get('MacroPLP_I_20250508')
    
    main(caso, profile, filter_files=args.files)
