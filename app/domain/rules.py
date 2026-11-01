"""Reglas puras del dominio (sin dependencias externas)."""
import os

from app.domain.errors import TransicionInvalida, ValidacionError
from app.domain.value_objects import Estado

# Flujo: Reportado -> En revision -> En atencion -> Atendido -> Cerrado
TRANSICIONES: dict[Estado, set[Estado]] = {
    Estado.REPORTADO: {Estado.EN_REVISION},
    Estado.EN_REVISION: {Estado.EN_ATENCION},
    Estado.EN_ATENCION: {Estado.ATENDIDO},
    Estado.ATENDIDO: {Estado.CERRADO},
    Estado.CERRADO: set(),
}
ESTADOS_ACTIVOS = {Estado.REPORTADO, Estado.EN_REVISION, Estado.EN_ATENCION}


def validar_transicion(actual: Estado, nuevo: Estado) -> None:
    if nuevo not in TRANSICIONES[actual]:
        raise TransicionInvalida(
            f"No se puede pasar de «{actual.value}» a «{nuevo.value}»."
        )


EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png"}
TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB
_FIRMA_JPG = b"\xff\xd8\xff"
_FIRMA_PNG = b"\x89PNG\r\n\x1a\n"


def validar_imagen(nombre: str, contenido: bytes) -> None:
    """HU-02: solo JPG/PNG. Se comprueba extension y firma real del archivo."""
    ext = os.path.splitext(nombre.lower())[1]
    if ext not in EXTENSIONES_PERMITIDAS:
        raise ValidacionError(f"«{nombre}»: formato no permitido (solo JPG o PNG).")
    if not contenido:
        raise ValidacionError(f"«{nombre}»: el archivo está vacío.")
    if len(contenido) > TAMANO_MAXIMO:
        raise ValidacionError(f"«{nombre}»: supera el tamaño máximo de 5 MB.")
    firma = _FIRMA_PNG if ext == ".png" else _FIRMA_JPG
    if not contenido.startswith(firma):
        raise ValidacionError(f"«{nombre}»: el contenido no corresponde a una imagen válida.")


def ordenar_por_prioridad(incidentes: list) -> list:
    """RF/HU-04: criticos primero; a igual gravedad, los mas recientes primero."""
    por_fecha = sorted(incidentes, key=lambda i: i.fecha_reporte, reverse=True)
    return sorted(por_fecha, key=lambda i: int(i.gravedad), reverse=True)
