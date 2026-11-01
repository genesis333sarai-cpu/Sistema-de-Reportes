"""Objetos de valor del dominio: inmutables y sin identidad propia."""
from dataclasses import dataclass
from enum import Enum, IntEnum

from app.domain.errors import ValidacionError


class Gravedad(IntEnum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4

    @property
    def etiqueta(self) -> str:
        return self.name.capitalize()


class Estado(str, Enum):
    REPORTADO = "Reportado"
    EN_REVISION = "En revisión"
    EN_ATENCION = "En atención"
    ATENDIDO = "Atendido"
    CERRADO = "Cerrado"


class Rol(str, Enum):
    CIUDADANO = "Ciudadano"
    FUNCIONARIO = "Funcionario municipal"
    RESPONSABLE = "Responsable de atención"
    ADMIN = "Administrador"


@dataclass(frozen=True)
class Coordenada:
    """Punto geografico valido (RF-03)."""
    latitud: float
    longitud: float

    def __post_init__(self):
        if not -90 <= self.latitud <= 90:
            raise ValidacionError("La latitud debe estar entre -90 y 90.")
        if not -180 <= self.longitud <= 180:
            raise ValidacionError("La longitud debe estar entre -180 y 180.")
