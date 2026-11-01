"""Raiz de composicion: el UNICO lugar donde se eligen las implementaciones concretas (DIP)."""
import os
from dataclasses import dataclass

from app.application.ports import MapaPort
from app.application.use_cases import (
    AgregarObservacionUseCase, AsignarResponsableUseCase, AutenticarUseCase, CambiarEstadoUseCase,
    ClasificarIncidenteUseCase, GestionarCategoriasUseCase, GestionarUsuariosUseCase,
    ListarCategoriasUseCase, ListarIncidentesUseCase, ListarResponsablesUseCase,
    ObtenerEstadisticasUseCase, ObtenerIncidenteUseCase, ObtenerUsuarioActivoUseCase,
    RegistrarCiudadanoUseCase, RegistrarIncidenteUseCase)
from app.domain.entities import Categoria, Usuario
from app.domain.value_objects import Rol
from app.infrastructure.maps.openstreetmap_adapter import OpenStreetMapAdapter
from app.infrastructure.persistence.repositories import (
    CategoriaRepositorySQL, IncidenteRepositorySQL, UsuarioRepositorySQL, crear_engine)
from app.infrastructure.security.hasher import HasherPBKDF2
from app.infrastructure.storage.almacen_archivos_local import AlmacenArchivosLocal


@dataclass
class Contenedor:
    carpeta_uploads: str
    mapa: MapaPort
    autenticar: AutenticarUseCase
    obtener_usuario: ObtenerUsuarioActivoUseCase
    registrar_ciudadano: RegistrarCiudadanoUseCase
    registrar_incidente: RegistrarIncidenteUseCase
    listar_incidentes: ListarIncidentesUseCase
    obtener_incidente: ObtenerIncidenteUseCase
    clasificar: ClasificarIncidenteUseCase
    asignar: AsignarResponsableUseCase
    cambiar_estado: CambiarEstadoUseCase
    observacion: AgregarObservacionUseCase
    estadisticas: ObtenerEstadisticasUseCase
    listar_categorias: ListarCategoriasUseCase
    listar_responsables: ListarResponsablesUseCase
    usuarios: GestionarUsuariosUseCase
    categorias: GestionarCategoriasUseCase


CATEGORIAS_INICIALES = [
    ("BASURA", "Acumulación de basura / microbasural"),
    ("QUEMA", "Quema de residuos / pastizales"),
    ("AGUA", "Contaminación de ríos y canales"),
    ("AIRE", "Contaminación del aire"),
    ("TALA", "Tala ilegal de árboles"),
    ("AREAS_VERDES", "Daño en áreas verdes"),
]
USUARIOS_DEMO = [  # SOLO para demostracion: cambiar las contrasenas antes de usar en serio
    ("1000001", "Lic. Carlos Pinto", "admin123", Rol.ADMIN),
    ("1000002", "Dra. Jimena Choque", "func123", Rol.FUNCIONARIO),
    ("1000003", "Ing. Raúl Vargas", "resp123", Rol.RESPONSABLE),
    ("1000004", "Alberto Mamani Soliz", "ciud123", Rol.CIUDADANO),
]


def construir(db_url: str = "sqlite:///vinto.db", carpeta_uploads: str = "uploads") -> Contenedor:
    engine = crear_engine(db_url)
    usuarios, categorias = UsuarioRepositorySQL(engine), CategoriaRepositorySQL(engine)
    incidentes = IncidenteRepositorySQL(engine)       # implementa escritura y consulta
    hasher, evidencias = HasherPBKDF2(), AlmacenArchivosLocal(carpeta_uploads)
    _sembrar(usuarios, categorias, hasher)
    return Contenedor(
        carpeta_uploads=carpeta_uploads, mapa=OpenStreetMapAdapter(),
        autenticar=AutenticarUseCase(usuarios, hasher),
        obtener_usuario=ObtenerUsuarioActivoUseCase(usuarios),
        registrar_ciudadano=RegistrarCiudadanoUseCase(usuarios, hasher),
        registrar_incidente=RegistrarIncidenteUseCase(incidentes, categorias, evidencias),
        listar_incidentes=ListarIncidentesUseCase(incidentes),
        obtener_incidente=ObtenerIncidenteUseCase(incidentes),
        clasificar=ClasificarIncidenteUseCase(incidentes, categorias),
        asignar=AsignarResponsableUseCase(incidentes, usuarios),
        cambiar_estado=CambiarEstadoUseCase(incidentes),
        observacion=AgregarObservacionUseCase(incidentes),
        estadisticas=ObtenerEstadisticasUseCase(incidentes, categorias),
        listar_categorias=ListarCategoriasUseCase(categorias),
        listar_responsables=ListarResponsablesUseCase(usuarios),
        usuarios=GestionarUsuariosUseCase(usuarios, hasher),
        categorias=GestionarCategoriasUseCase(categorias))


def _sembrar(usuarios, categorias, hasher) -> None:
    if not categorias.listar():
        for codigo, nombre in CATEGORIAS_INICIALES:
            categorias.guardar(Categoria(codigo=codigo, nombre=nombre))
    if not usuarios.listar() and os.getenv("VINTO_SIN_DEMO") != "1":
        for ci, nombre, pw, rol in USUARIOS_DEMO:
            usuarios.guardar(Usuario(ci=ci, nombre=nombre, password_hash=hasher.hash(pw), rol=rol))
