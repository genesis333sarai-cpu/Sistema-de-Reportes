from pathlib import Path
import importlib.util

spec = importlib.util.find_spec("vbuild")

if spec is None or spec.origin is None:
    raise FileNotFoundError("No se encontró vbuild.")

archivo = Path(spec.origin)

contenido = archivo.read_text(encoding="utf-8")

# Agregar el import si falta
if "import importlib" not in contenido:
    lineas = contenido.splitlines()

    # insertar después del último import
    indice = 0
    for i, linea in enumerate(lineas):
        if linea.startswith("import ") or linea.startswith("from "):
            indice = i

    lineas.insert(indice + 1, "import importlib")

    contenido = "\n".join(lineas)

# Compatibilidad con versiones antiguas
contenido = contenido.replace(
    'pkgutil.find_loader("lesscpy")',
    'importlib.util.find_spec("lesscpy")'
)

contenido = contenido.replace(
    'pkgutil.find_loader("scss")',
    'importlib.util.find_spec("scss")'
)

contenido = contenido.replace(
    'pkgutil.find_loader("closure")',
    'importlib.util.find_spec("closure")'
)

archivo.write_text(contenido, encoding="utf-8")

print("vbuild corregido.")