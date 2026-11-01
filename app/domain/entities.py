"""Entidades del dominio. No conocen NiceGUI, SQLModel ni el sistema de archivos."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.domain.errors import ValidacionError
from app.domain.rules import validar_transicion
from app.domain.value_objects import Coordenada, Estado, Gravedad, Rol


@dataclass
class Usuario:
    ci: str
    nombre: str
    password_hash: str
    rol: Rol
    activo: bool = True
    telefono: str = ""
    email: str = ""
    id: Optional[int] = None


@dataclass
class Categoria:
    codigo: str
    nombre: str
    activa: bool = True
    id: Optional[int] = None


@dataclass
class HistorialEstado:
    """Registro de auditoria (RF-06, RNF-12). Nunca se elimina."""
    fecha: datetime
    usuario: str
    accion: str
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    observacion: str = ""


@dataclass
class Observacion:
    fecha: datetime
    autor: str
    texto: str
    publica: bool = False  # solo las publicas las ve el ciudadano (HU-03)


@dataclass
class Incidente:
    categoria_id: int
    categoria_codigo: str
    descripcion: str
    gravedad: Gravedad
    zona: str
    direccion: str
    referencia: str
    coordenada: Optional[Coordenada]
    reportante_id: int
    codigo: str = ""
    estado: Estado = Estado.REPORTADO
    fecha_reporte: datetime = field(default_factory=lambda: datetime.now(timezone.utc))    
    evidencias: list = field(default_factory=list)
    responsable_id: Optional[int] = None
    fecha_atendido: Optional[datetime] = None
    historial: list = field(default_factory=list)
    observaciones: list = field(default_factory=list)
    id: Optional[int] = None

    def __post_init__(self):
        self.gravedad = Gravedad(self.gravedad)
        self.estado = Estado(self.estado)

    # ---- validacion (las variantes por categoria la extienden: OCP) ----
    def validar(self) -> None:
        if not self.categoria_id:
            raise ValidacionError("Debe seleccionar el tipo de incidente.")
        if len(self.descripcion.strip()) < 10:
            raise ValidacionError("La descripción debe tener al menos 10 caracteres.")
        if not self.zona.strip():
            raise ValidacionError("Debe indicar la zona del incidente.")
        if not self.direccion.strip():
            raise ValidacionError("Debe indicar la dirección o referencia del lugar.")
        if self.coordenada is None:
            raise ValidacionError("Debe marcar la ubicación del incidente en el mapa.")

    # ---- comportamiento ----
    def agregar_evidencia(self, ruta: str) -> None:
        self.evidencias.append(ruta)

    def registrar_creacion(self, usuario: str) -> None:
        self.historial.append(HistorialEstado(
            self.fecha_reporte, usuario, "Registro del incidente",
            None, Estado.REPORTADO.value, "Incidente reportado."))

    def cambiar_estado(self, nuevo: Estado, usuario: str, observacion: str = "") -> None:
        validar_transicion(self.estado, nuevo)
        ahora = datetime.now(timezone.utc)
        anterior = self.estado
        self.estado = nuevo
        if nuevo == Estado.ATENDIDO:
            self.fecha_atendido = ahora
        self.historial.append(HistorialEstado(
            ahora, usuario, "Cambio de estado", anterior.value, nuevo.value, observacion))

    def cambiar_gravedad(self, nueva: Gravedad, usuario: str, motivo: str = "") -> None:
        nueva = Gravedad(nueva)
        anterior = self.gravedad
        self.gravedad = nueva
        try:
            self.validar()  # siempre: puede violar reglas propias de la categoria
        except ValidacionError:
            self.gravedad = anterior
            raise
        if nueva == anterior:
            return
        self.historial.append(HistorialEstado(
            datetime.now(timezone.utc), usuario, "Cambio de gravedad", None, None,
            f"{anterior.etiqueta} → {nueva.etiqueta}. {motivo}".strip()))

    def asignar(self, responsable_id: int, responsable_nombre: str, usuario: str) -> None:
        self.responsable_id = responsable_id
        self.historial.append(HistorialEstado(
            datetime.now(timezone.utc), usuario, "Asignación de responsable", None, None,
            f"Responsable: {responsable_nombre}"))

    def agregar_observacion(self, autor: str, texto: str, publica: bool = False) -> None:
        if not texto.strip():
            raise ValidacionError("La observación no puede estar vacía.")
        self.observaciones.append(Observacion(Observacion(datetime.now(timezone.utc), autor, texto.strip(), publica)))

    def observaciones_para(self, rol: Rol) -> list:
        if rol == Rol.CIUDADANO:
            return [o for o in self.observaciones if o.publica]
        return list(self.observaciones)
