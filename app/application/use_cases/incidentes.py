from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.application.ports import (
    AlmacenEvidenciaPort, CategoriaRepository, ConsultaIncidentes, FiltroIncidentes,
    IncidenteRepository, UsuarioRepository)
from app.application.use_cases._comun import exigir_rol
from app.domain.entities import HistorialEstado, Incidente, Usuario
from app.domain.errors import NoEncontrado, PermisoDenegado, ValidacionError
from app.domain.factories import IncidenteFactory
from app.domain.rules import ordenar_por_prioridad, validar_imagen
from app.domain.value_objects import Coordenada, Estado, Gravedad, Rol

STAFF = (Rol.FUNCIONARIO, Rol.ADMIN)


@dataclass
class RegistrarIncidenteCmd:
    reportante: Usuario
    categoria_id: int
    descripcion: str
    gravedad: Gravedad
    zona: str
    direccion: str
    referencia: str = ""
    coordenada: Optional[Coordenada] = None
    fotos: list = field(default_factory=list)  # lista de (nombre, bytes)


class RegistrarIncidenteUseCase:

    def __init__(self, incidentes: IncidenteRepository, categorias: CategoriaRepository,
                 evidencias: AlmacenEvidenciaPort):
        self._incidentes, self._categorias, self._evidencias = incidentes, categorias, evidencias

    def ejecutar(self, cmd: RegistrarIncidenteCmd) -> Incidente:
        categoria = self._categorias.obtener(cmd.categoria_id) if cmd.categoria_id else None
        if categoria is None or not categoria.activa:
            raise ValidacionError("Debe seleccionar un tipo de incidente válido.")
        incidente = IncidenteFactory.crear(
            categoria.codigo, categoria_id=categoria.id, descripcion=cmd.descripcion,
            gravedad=cmd.gravedad, zona=cmd.zona, direccion=cmd.direccion,
            referencia=cmd.referencia, coordenada=cmd.coordenada,
            reportante_id=cmd.reportante.id)
        for nombre, contenido in cmd.fotos:      # validar ANTES de guardar nada
            validar_imagen(nombre, contenido)
        anio = incidente.fecha_reporte.year
        incidente.codigo = f"VIN-{anio}-{self._incidentes.siguiente_numero(anio):03d}"
        incidente.registrar_creacion(cmd.reportante.nombre)
        for nombre, contenido in cmd.fotos:
            incidente.agregar_evidencia(self._evidencias.guardar(incidente.codigo, nombre, contenido))
        return self._incidentes.guardar(incidente)


def _puede_ver(actor: Usuario, inc: Incidente) -> bool:
    if actor.rol in STAFF:
        return True
    if actor.rol == Rol.CIUDADANO:
        return inc.reportante_id == actor.id
    if actor.rol == Rol.RESPONSABLE:
        return inc.responsable_id == actor.id
    return False


class ListarIncidentesUseCase:
    """RF-05: lista con filtros. El alcance depende del rol; el orden es por prioridad."""

    def __init__(self, consulta: ConsultaIncidentes):
        self._consulta = consulta

    def ejecutar(self, actor: Usuario, filtro: Optional[FiltroIncidentes] = None) -> list[Incidente]:
        filtro = filtro or FiltroIncidentes()
        if actor.rol == Rol.CIUDADANO:
            filtro.reportante_id = actor.id
        elif actor.rol == Rol.RESPONSABLE:
            filtro.responsable_id = actor.id
        return ordenar_por_prioridad(self._consulta.listar(filtro))


class ObtenerIncidenteUseCase:
    def __init__(self, incidentes: IncidenteRepository):
        self._incidentes = incidentes

    def ejecutar(self, actor: Usuario, codigo: str) -> Incidente:
        inc = self._incidentes.obtener_por_codigo(codigo)
        if inc is None or not _puede_ver(actor, inc):
            # mismo error: no se revela la existencia de reportes ajenos (RNF-04)
            raise NoEncontrado("El incidente no existe o no tiene acceso a él.")
        return inc


class ClasificarIncidenteUseCase:
    """HU-04: el funcionario confirma/modifica categoria y gravedad."""

    def __init__(self, incidentes: IncidenteRepository, categorias: CategoriaRepository):
        self._incidentes, self._categorias = incidentes, categorias

    def ejecutar(self, actor: Usuario, codigo: str, gravedad: Gravedad,
                 categoria_id: Optional[int] = None, motivo: str = "") -> Incidente:
        exigir_rol(actor, *STAFF)
        inc = self._incidentes.obtener_por_codigo(codigo)
        if inc is None:
            raise NoEncontrado("El incidente no existe.")
        if categoria_id and categoria_id != inc.categoria_id:
            cat = self._categorias.obtener(categoria_id)
            if cat is None or not cat.activa:
                raise ValidacionError("La categoría seleccionada no es válida.")
            inc = IncidenteFactory.reconstruir(cat.codigo, **{
                **{k: getattr(inc, k) for k in inc.__dataclass_fields__ if k != "categoria_codigo"},
                "categoria_id": cat.id})
            inc.historial.append(HistorialEstado(
                datetime.now(timezone.utc), actor.nombre, "Cambio de categoría", None, None,
                f"Nueva categoría: {cat.nombre}. {motivo}".strip()))
        inc.cambiar_gravedad(gravedad, actor.nombre, motivo)
        return self._incidentes.guardar(inc)


class AsignarResponsableUseCase:
    """HU-06 / RF-07. Al asignar, el incidente avanza hasta 'En atencion' paso a paso."""

    def __init__(self, incidentes: IncidenteRepository, usuarios: UsuarioRepository):
        self._incidentes, self._usuarios = incidentes, usuarios

    def ejecutar(self, actor: Usuario, codigo: str, responsable_id: int) -> Incidente:
        exigir_rol(actor, *STAFF)
        inc = self._incidentes.obtener_por_codigo(codigo)
        if inc is None:
            raise NoEncontrado("El incidente no existe.")
        resp = self._usuarios.obtener(responsable_id)
        if resp is None or resp.rol != Rol.RESPONSABLE or not resp.activo:
            raise ValidacionError("Solo se pueden asignar responsables activos.")
        if inc.estado in (Estado.ATENDIDO, Estado.CERRADO):
            raise ValidacionError("No se puede reasignar un incidente ya atendido o cerrado.")
        inc.asignar(resp.id, resp.nombre, actor.nombre)
        if inc.estado == Estado.REPORTADO:
            inc.cambiar_estado(Estado.EN_REVISION, actor.nombre, "Revisión iniciada al asignar responsable.")
        if inc.estado == Estado.EN_REVISION:
            inc.cambiar_estado(Estado.EN_ATENCION, actor.nombre, "Atención iniciada al asignar responsable.")
        return self._incidentes.guardar(inc)


class CambiarEstadoUseCase:
    """HU-07 / RF-06."""

    def __init__(self, incidentes: IncidenteRepository):
        self._incidentes = incidentes

    @staticmethod
    def puede_actuar(actor: Usuario, inc: Incidente) -> bool:
        if actor.rol in STAFF:
            return True
        return actor.rol == Rol.RESPONSABLE and inc.responsable_id == actor.id

    def ejecutar(self, actor: Usuario, codigo: str, nuevo: Estado, observacion: str = "") -> Incidente:
        inc = self._incidentes.obtener_por_codigo(codigo)
        if inc is None:
            raise NoEncontrado("El incidente no existe.")
        if not self.puede_actuar(actor, inc):
            raise PermisoDenegado("Solo el funcionario o el responsable asignado pueden cambiar el estado.")
        nuevo = Estado(nuevo)
        if nuevo == Estado.EN_ATENCION and inc.responsable_id is None:
            raise ValidacionError("Asigne un responsable antes de iniciar la atención.")
        inc.cambiar_estado(nuevo, actor.nombre, observacion.strip())
        return self._incidentes.guardar(inc)


class AgregarObservacionUseCase:
    def __init__(self, incidentes: IncidenteRepository):
        self._incidentes = incidentes

    def ejecutar(self, actor: Usuario, codigo: str, texto: str, publica: bool = False) -> Incidente:
        inc = self._incidentes.obtener_por_codigo(codigo)
        if inc is None:
            raise NoEncontrado("El incidente no existe.")
        if not CambiarEstadoUseCase.puede_actuar(actor, inc):
            raise PermisoDenegado("No puede registrar observaciones en este incidente.")
        inc.agregar_observacion(actor.nombre, texto, publica)
        return self._incidentes.guardar(inc)
