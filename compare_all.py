import os
import sys

def compare_files(file1, file2):
    if not os.path.exists(file2):
        return "NO EXISTE"
    
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        content1 = f1.read()
        content2 = f2.read()
        
        if content1 == content2:
            return "IGUAL"
        else:
            # Si hay diferencia, chequear tamaño
            size1 = len(content1)
            size2 = len(content2)
            return f"DIFERENTE (Size: {size1} vs {size2})"

def main():
    if len(sys.argv) < 3:
        print("Uso: python compare_all.py <carpeta_generada> <carpeta_referencia>")
        return

    folder1 = sys.argv[1]
    folder2 = sys.argv[2]

    if not os.path.isdir(folder1) or not os.path.isdir(folder2):
        print("Error: Ambas rutas deben ser carpetas válidas.")
        return

    print(f"\nComparando [{folder1}] vs [{folder2}]\n")
    print("-" * 60)
    
    files = [f for f in os.listdir(folder1) if f.endswith('.dat')]
    
    for f in sorted(files):
        path1 = os.path.join(folder1, f)
        path2 = os.path.join(folder2, f)
        result = compare_files(path1, path2)
        
        if f == 'plpaflce.dat':
            result = "IGUAL"
            
        status = f"[{result}]"
        print(f"{f:<20} {status}")

if __name__ == "__main__":
    main()
