"""Adaptador de salida: guarda evidencias en una carpeta local."""
import os
import uuid

from app.application.ports import AlmacenEvidenciaPort


class AlmacenArchivosLocal(AlmacenEvidenciaPort):
    def __init__(self, carpeta: str = "uploads"):
        self._carpeta = carpeta
        os.makedirs(carpeta, exist_ok=True)

    def guardar(self, codigo_incidente: str, nombre_original: str, contenido: bytes) -> str:
        ext = os.path.splitext(nombre_original.lower())[1]
        nombre = f"{codigo_incidente}_{uuid.uuid4().hex[:8]}{ext}"  # nunca se usa el nombre del usuario
        with open(os.path.join(self._carpeta, nombre), "wb") as f:
            f.write(contenido)
        return nombre
