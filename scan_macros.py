import os
import re

macro_dir = r'C:\Users\ep_bvaldebenito\Downloads\macros'
macros = [
    'MacroPLP_I_20220414.xla',
    'MacroPLP_I_20221116_cen.xla',
    'MacroPLP_I_20250508.xla',
    'MacroPLP_I_20250508_cen_nueva.xla',
    'MacroPLP_I_20250508v.xla'
]

def scan_macro(filename):
    path = os.path.join(macro_dir, filename)
    if not os.path.exists(path): return {"error": "No encontrado"}
    
    results = {"filename": filename}
    try:
        with open(path, 'rb') as f:
            content = f.read()
            
            # Buscar la firma de etiquetas extra
            if b",FV, EO, CS" in content:
                results["has_extra_tags"] = True
            else:
                results["has_extra_tags"] = False
                
            # Buscar si hay referencias a Mes inicial o desfases
            # Intentamos decodificar como utf-16 (comun en VBA) o latin-1
            text_samples = []
            for encoding in ['latin-1', 'utf-16le']:
                try:
                    text = content.decode(encoding, errors='ignore')
                    # Buscamos patrones de numeros de etapas o saltos
                    if "Etapas" in text:
                        text_samples.append("Mencion de Etapas detectada")
                except:
                    pass
            results["notes"] = ", ".join(set(text_samples))
            
    except Exception as e:
        results["error"] = str(e)
    return results

print("RESULTADOS DE ESCANEO DE MACROS ORIGINALES:")
print(f"{'Archivo':<35} | {'Extra Tags':<10} | {'Notas'}")
print("-" * 70)
for m in macros:
    res = scan_macro(m)
    print(f"{res['filename']:<35} | {str(res.get('has_extra_tags','?')):<10} | {res.get('notes','')}")
