from pathlib import Path
import importlib.util

archivo = Path(".venv/Lib/site-packages/vbuild/__init__.py")

if not archivo.exists():
    raise FileNotFoundError("No se encontró vbuild. Instala primero las dependencias.")

contenido = archivo.read_text(encoding="utf-8")

if "pkgutil.find_loader" in contenido:
    contenido = contenido.replace(
        "import re, os, json, glob, itertools, traceback, subprocess, pkgutil",
        "import re, os, json, glob, itertools, traceback, subprocess, pkgutil\nimport importlib.util"
    )

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
    print("Corrección de vbuild aplicada correctamente.")
else:
    print("vbuild ya está corregido.")