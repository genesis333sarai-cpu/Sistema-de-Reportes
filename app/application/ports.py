"""Puertos: interfaces que la aplicacion necesita. Las implementa la infraestructura (DIP)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.domain.entities import Categoria, Incidente, Usuario
from app.domain.value_objects import Coordenada, Estado, Gravedad, Rol


@dataclass
class FiltroIncidentes:
    categoria_id: Optional[int] = None
    gravedad: Optional[Gravedad] = None
    estado: Optional[Estado] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    zona: str = ""
    reportante_id: Optional[int] = None
    responsable_id: Optional[int] = None


@dataclass
class Marcador:
    coordenada: Coordenada
    titulo: str
    detalle: str
    color: str


class IncidenteRepository(ABC):
    @abstractmethod
    def guardar(self, incidente: Incidente) -> Incidente: 
        pass
    @abstractmethod
    def obtener_por_codigo(self, codigo: str) -> Optional[Incidente]: 
        pass
    @abstractmethod
    def siguiente_numero(self, anio: int) -> int: 
        pass


class ConsultaIncidentes(ABC):
    @abstractmethod
    def listar(self, filtro: FiltroIncidentes) -> list[Incidente]: 
        pass


class UsuarioRepository(ABC):
    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario: 
        pass
    @abstractmethod
    def obtener(self, usuario_id: int) -> Optional[Usuario]: 
        pass
    @abstractmethod
    def obtener_por_ci(self, ci: str) -> Optional[Usuario]: 
        pass
    @abstractmethod
    def listar(self, rol: Optional[Rol] = None, solo_activos: bool = False) -> list[Usuario]: 
        pass


class CategoriaRepository(ABC):
    @abstractmethod
    def guardar(self, categoria: Categoria) -> Categoria: 
        pass
    @abstractmethod
    def obtener(self, categoria_id: int) -> Optional[Categoria]: 
        pass
    @abstractmethod
    def obtener_por_codigo(self, codigo: str) -> Optional[Categoria]: 
        pass
    @abstractmethod
    def listar(self, solo_activas: bool = False) -> list[Categoria]: 
        pass
    @abstractmethod
    def en_uso(self, categoria_id: int) -> bool: 
        pass
    @abstractmethod
    def eliminar(self, categoria_id: int) -> None: 
        pass


class AlmacenEvidenciaPort(ABC):
    @abstractmethod
    def guardar(self, codigo_incidente: str, nombre_original: str, contenido: bytes) -> str:
        """Guarda la imagen y devuelve su ruta relativa."""


class MapaPort(ABC):
    @abstractmethod
    def centro_por_defecto(self) -> Coordenada: 
        pass
    @abstractmethod
    def marcadores(self, incidentes: list[Incidente]) -> list[Marcador]: 
        pass


class HasherPort(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: 
        pass
    @abstractmethod
    def verificar(self, password: str, hash_guardado: str) -> bool: 
        pass
