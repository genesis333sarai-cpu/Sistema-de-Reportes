"""Adaptadores de salida: implementan los puertos de repositorio con SQLModel."""
from datetime import datetime, time
from typing import Optional

from sqlmodel import Session, SQLModel, col, create_engine, select

from app.application.ports import (
    CategoriaRepository, ConsultaIncidentes, FiltroIncidentes, IncidenteRepository, UsuarioRepository)
from app.domain.entities import Categoria, HistorialEstado, Incidente, Observacion, Usuario
from app.domain.factories import IncidenteFactory
from app.domain.value_objects import Coordenada, Rol
from app.infrastructure.persistence.models import CategoriaDB, IncidenteDB, UsuarioDB


def crear_engine(url: str = "sqlite:///vinto.db"):
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    SQLModel.metadata.create_all(engine)
    return engine


def _dt(valor: str) -> datetime:
    return datetime.fromisoformat(valor)


class UsuarioRepositorySQL(UsuarioRepository):
    def __init__(self, engine):
        self._engine = engine

    @staticmethod
    def _dominio(r: UsuarioDB) -> Usuario:
        return Usuario(id=r.id, ci=r.ci, nombre=r.nombre, password_hash=r.password_hash,
                       rol=Rol(r.rol), activo=r.activo, telefono=r.telefono, email=r.email)

    def guardar(self, u: Usuario) -> Usuario:
        with Session(self._engine) as s:
            r = s.get(UsuarioDB, u.id) if u.id else UsuarioDB(ci=u.ci, nombre=u.nombre, password_hash="", rol="")
            r.ci, r.nombre, r.password_hash, r.rol = u.ci, u.nombre, u.password_hash, u.rol.value
            r.activo, r.telefono, r.email = u.activo, u.telefono, u.email
            s.add(r)
            s.commit()
            s.refresh(r)
            return self._dominio(r)

    def obtener(self, usuario_id: int) -> Optional[Usuario]:
        with Session(self._engine) as s:
            r = s.get(UsuarioDB, usuario_id)
            return self._dominio(r) if r else None

    def obtener_por_ci(self, ci: str) -> Optional[Usuario]:
        with Session(self._engine) as s:
            r = s.exec(select(UsuarioDB).where(UsuarioDB.ci == ci)).first()
            return self._dominio(r) if r else None

    def listar(self, rol: Optional[Rol] = None, solo_activos: bool = False) -> list[Usuario]:
        with Session(self._engine) as s:
            q = select(UsuarioDB)
            if rol:
                q = q.where(UsuarioDB.rol == rol.value)
            if solo_activos:
                q = q.where(UsuarioDB.activo == True)  # noqa: E712
            return [self._dominio(r) for r in s.exec(q.order_by(UsuarioDB.nombre)).all()]


class CategoriaRepositorySQL(CategoriaRepository):
    def __init__(self, engine):
        self._engine = engine

    @staticmethod
    def _dominio(r: CategoriaDB) -> Categoria:
        return Categoria(id=r.id, codigo=r.codigo, nombre=r.nombre, activa=r.activa)

    def guardar(self, c: Categoria) -> Categoria:
        with Session(self._engine) as s:
            r = s.get(CategoriaDB, c.id) if c.id else CategoriaDB(codigo=c.codigo, nombre=c.nombre)
            r.codigo, r.nombre, r.activa = c.codigo, c.nombre, c.activa
            s.add(r)
            s.commit()
            s.refresh(r)
            return self._dominio(r)

    def obtener(self, categoria_id: int) -> Optional[Categoria]:
        with Session(self._engine) as s:
            r = s.get(CategoriaDB, categoria_id)
            return self._dominio(r) if r else None

    def obtener_por_codigo(self, codigo: str) -> Optional[Categoria]:
        with Session(self._engine) as s:
            r = s.exec(select(CategoriaDB).where(CategoriaDB.codigo == codigo)).first()
            return self._dominio(r) if r else None

    def listar(self, solo_activas: bool = False) -> list[Categoria]:
        with Session(self._engine) as s:
            q = select(CategoriaDB)
            if solo_activas:
                q = q.where(CategoriaDB.activa == True)  # noqa: E712
            return [self._dominio(r) for r in s.exec(q.order_by(CategoriaDB.nombre)).all()]

    def en_uso(self, categoria_id: int) -> bool:
        with Session(self._engine) as s:
            return s.exec(select(IncidenteDB.id).where(IncidenteDB.categoria_id == categoria_id)).first() is not None

    def eliminar(self, categoria_id: int) -> None:
        with Session(self._engine) as s:
            r = s.get(CategoriaDB, categoria_id)
            if r:
                s.delete(r)
                s.commit()


class IncidenteRepositorySQL(IncidenteRepository, ConsultaIncidentes):

    def __init__(self, engine):
        self._engine = engine

    # ---- mapeo dominio <-> tabla ----
    @staticmethod
    def _dominio(r: IncidenteDB) -> Incidente:
        coord = Coordenada(r.latitud, r.longitud) if r.latitud is not None and r.longitud is not None else None
        return IncidenteFactory.reconstruir(
            r.categoria_codigo, id=r.id, codigo=r.codigo, categoria_id=r.categoria_id,
            descripcion=r.descripcion, gravedad=r.gravedad, estado=r.estado, zona=r.zona,
            direccion=r.direccion, referencia=r.referencia, coordenada=coord,
            reportante_id=r.reportante_id, responsable_id=r.responsable_id,
            fecha_reporte=r.fecha_reporte, fecha_atendido=r.fecha_atendido,
            evidencias=list(r.evidencias or []),
            historial=[HistorialEstado(_dt(h["fecha"]), h["usuario"], h["accion"], h.get("estado_anterior"),
                                       h.get("estado_nuevo"), h.get("observacion", "")) for h in (r.historial or [])],
            observaciones=[Observacion(_dt(o["fecha"]), o["autor"], o["texto"], o["publica"])
                           for o in (r.observaciones or [])])

    @staticmethod
    def _volcar(i: Incidente, r: IncidenteDB) -> None:
        r.codigo, r.categoria_id, r.categoria_codigo = i.codigo, i.categoria_id, i.categoria_codigo
        r.descripcion, r.gravedad, r.estado = i.descripcion, int(i.gravedad), i.estado.value
        r.zona, r.direccion, r.referencia = i.zona, i.direccion, i.referencia
        r.latitud = i.coordenada.latitud if i.coordenada else None
        r.longitud = i.coordenada.longitud if i.coordenada else None
        r.reportante_id, r.responsable_id = i.reportante_id, i.responsable_id
        r.fecha_reporte, r.fecha_atendido = i.fecha_reporte, i.fecha_atendido
        r.evidencias = list(i.evidencias)
        r.historial = [{"fecha": h.fecha.isoformat(), "usuario": h.usuario, "accion": h.accion,
                        "estado_anterior": h.estado_anterior, "estado_nuevo": h.estado_nuevo,
                        "observacion": h.observacion} for h in i.historial]
        r.observaciones = [{"fecha": o.fecha.isoformat(), "autor": o.autor, "texto": o.texto,
                            "publica": o.publica} for o in i.observaciones]

    # ---- IncidenteRepository ----
    def guardar(self, incidente: Incidente) -> Incidente:
        with Session(self._engine) as s:
            r = s.get(IncidenteDB, incidente.id) if incidente.id else IncidenteDB(
                codigo="", categoria_id=0, categoria_codigo="", descripcion="", gravedad=1, estado="",
                zona="", direccion="", reportante_id=0, fecha_reporte=incidente.fecha_reporte)
            self._volcar(incidente, r)
            s.add(r)
            s.commit()
            s.refresh(r)
            return self._dominio(r)

    def obtener_por_codigo(self, codigo: str) -> Optional[Incidente]:
        with Session(self._engine) as s:
            r = s.exec(select(IncidenteDB).where(IncidenteDB.codigo == codigo)).first()
            return self._dominio(r) if r else None

    def siguiente_numero(self, anio: int) -> int:
        with Session(self._engine) as s:
            prefijo = f"VIN-{anio}-"
            n = len(s.exec(select(IncidenteDB.id).where(col(IncidenteDB.codigo).startswith(prefijo))).all())
            return n + 1

    # ---- ConsultaIncidentes ----
    def listar(self, f: FiltroIncidentes) -> list[Incidente]:
        with Session(self._engine) as s:
            q = select(IncidenteDB)
            if f.categoria_id:
                q = q.where(IncidenteDB.categoria_id == f.categoria_id)
            if f.gravedad:
                q = q.where(IncidenteDB.gravedad == int(f.gravedad))
            if f.estado:
                q = q.where(IncidenteDB.estado == f.estado.value)
            if f.fecha_desde:
                q = q.where(IncidenteDB.fecha_reporte >= datetime.combine(f.fecha_desde, time.min))
            if f.fecha_hasta:
                q = q.where(IncidenteDB.fecha_reporte <= datetime.combine(f.fecha_hasta, time.max))
            if f.zona.strip():
                q = q.where(col(IncidenteDB.zona).icontains(f.zona.strip()))
            if f.reportante_id:
                q = q.where(IncidenteDB.reportante_id == f.reportante_id)
            if f.responsable_id:
                q = q.where(IncidenteDB.responsable_id == f.responsable_id)
            return [self._dominio(r) for r in s.exec(q).all()]
