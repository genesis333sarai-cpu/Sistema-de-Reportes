"""Dobles de prueba en memoria: implementan los mismos puertos que la infraestructura (LSP)."""
import copy
from typing import Optional

from app.application.ports import (
    AlmacenEvidenciaPort, CategoriaRepository, ConsultaIncidentes, FiltroIncidentes,
    IncidenteRepository, UsuarioRepository)
from app.domain.entities import Categoria, Incidente, Usuario
from app.domain.value_objects import Rol
from app.infrastructure.security.hasher import HasherPBKDF2


class UsuarioRepoMem(UsuarioRepository):
    def __init__(self):
        self.d, self._n = {}, 0

    def guardar(self, u):
        if not u.id:
            self._n += 1
            u.id = self._n
        self.d[u.id] = copy.deepcopy(u)
        return copy.deepcopy(u)

    def obtener(self, uid):
        return copy.deepcopy(self.d.get(uid))

    def obtener_por_ci(self, ci):
        return next((copy.deepcopy(u) for u in self.d.values() if u.ci == ci), None)

    def listar(self, rol=None, solo_activos=False):
        return [copy.deepcopy(u) for u in self.d.values()
                if (rol is None or u.rol == rol) and (not solo_activos or u.activo)]


class CategoriaRepoMem(CategoriaRepository):
    def __init__(self):
        self.d, self._n, self.usadas = {}, 0, set()

    def guardar(self, c):
        if not c.id:
            self._n += 1
            c.id = self._n
        self.d[c.id] = copy.deepcopy(c)
        return copy.deepcopy(c)

    def obtener(self, cid):
        return copy.deepcopy(self.d.get(cid))

    def obtener_por_codigo(self, codigo):
        return next((copy.deepcopy(c) for c in self.d.values() if c.codigo == codigo), None)

    def listar(self, solo_activas=False):
        return [copy.deepcopy(c) for c in self.d.values() if not solo_activas or c.activa]

    def en_uso(self, cid):
        return cid in self.usadas

    def eliminar(self, cid):
        self.d.pop(cid, None)


class IncidenteRepoMem(IncidenteRepository, ConsultaIncidentes):
    def __init__(self):
        self.d, self._n = {}, 0

    def guardar(self, i):
        if not i.id:
            self._n += 1
            i.id = self._n
        self.d[i.codigo] = copy.deepcopy(i)
        return copy.deepcopy(i)

    def obtener_por_codigo(self, codigo):
        return copy.deepcopy(self.d.get(codigo))

    def siguiente_numero(self, anio):
        return sum(1 for c in self.d if c.startswith(f"VIN-{anio}-")) + 1

    def listar(self, f: FiltroIncidentes):
        r = list(self.d.values())
        if f.categoria_id: r = [i for i in r if i.categoria_id == f.categoria_id]
        if f.gravedad: r = [i for i in r if i.gravedad == f.gravedad]
        if f.estado: r = [i for i in r if i.estado == f.estado]
        if f.fecha_desde: r = [i for i in r if i.fecha_reporte.date() >= f.fecha_desde]
        if f.fecha_hasta: r = [i for i in r if i.fecha_reporte.date() <= f.fecha_hasta]
        if f.zona.strip(): r = [i for i in r if f.zona.strip().lower() in i.zona.lower()]
        if f.reportante_id: r = [i for i in r if i.reportante_id == f.reportante_id]
        if f.responsable_id: r = [i for i in r if i.responsable_id == f.responsable_id]
        return copy.deepcopy(r)


class AlmacenMem(AlmacenEvidenciaPort):
    def __init__(self):
        self.archivos = {}

    def guardar(self, codigo, nombre, contenido):
        ruta = f"{codigo}_{len(self.archivos)}.{nombre.rsplit('.', 1)[-1]}"
        self.archivos[ruta] = contenido
        return ruta


class Mundo:
    """Ensambla un sistema completo en memoria para las pruebas."""

    def __init__(self):
        self.hasher = HasherPBKDF2(iteraciones=1000)
        self.usuarios, self.categorias = UsuarioRepoMem(), CategoriaRepoMem()
        self.incidentes, self.almacen = IncidenteRepoMem(), AlmacenMem()
        mk = lambda ci, n, rol: self.usuarios.guardar(Usuario(ci=ci, nombre=n, password_hash=self.hasher.hash("secreto1"), rol=rol))
        self.ciudadano = mk("111", "Ana Ciudadana", Rol.CIUDADANO)
        self.otro = mk("112", "Otro Vecino", Rol.CIUDADANO)
        self.funcionario = mk("222", "Fabio Funcionario", Rol.FUNCIONARIO)
        self.responsable = mk("333", "Raul Responsable", Rol.RESPONSABLE)
        self.otro_resp = mk("334", "Rosa Responsable", Rol.RESPONSABLE)
        self.admin = mk("444", "Alicia Admin", Rol.ADMIN)
        self.cat_basura = self.categorias.guardar(Categoria(codigo="BASURA", nombre="Basura"))
        self.cat_quema = self.categorias.guardar(Categoria(codigo="QUEMA", nombre="Quema"))
        self.cat_agua = self.categorias.guardar(Categoria(codigo="AGUA", nombre="Agua"))
