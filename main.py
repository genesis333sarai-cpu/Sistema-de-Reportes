"""Punto de entrada:  python main.py   ->  http://localhost:8080"""
import logging
import os

from nicegui import app, ui

from app.container import construir
from app.ui.pages import registrar_paginas

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

contenedor = construir(
    db_url=os.getenv("VINTO_DB", "sqlite:///vinto.db"),
    carpeta_uploads=os.getenv("VINTO_UPLOADS", "uploads"))
app.add_static_files("/uploads", contenedor.carpeta_uploads)   # para mostrar las evidencias
registrar_paginas(contenedor)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Incidentes Vinto", favicon="🌿", port=int(os.getenv("PORT", "8080")),
           storage_secret=os.getenv("VINTO_SECRET", "cambie-esta-clave-en-produccion"), reload=False)
