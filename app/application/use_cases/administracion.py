import logging
from typing import Optional

from app.application.ports import CategoriaRepository, HasherPort, UsuarioRepository
from app.application.use_cases._comun import exigir_rol
from app.domain.entities import Categoria, Usuario
from app.domain.errors import NoEncontrado, ReglaNegocio, ValidacionError
from app.domain.value_objects import Rol

log = logging.getLogger("auditoria")  # HU-09: los cambios administrativos quedan registrados


class ListarResponsablesUseCase:
    def __init__(self, usuarios: UsuarioRepository):
        self._usuarios = usuarios

    def ejecutar(self) -> list[Usuario]:
        return self._usuarios.listar(rol=Rol.RESPONSABLE, solo_activos=True)


class ListarCategoriasUseCase:
    def __init__(self, categorias: CategoriaRepository):
        self._categorias = categorias

    def ejecutar(self, solo_activas: bool = False) -> list[Categoria]:
        return self._categorias.listar(solo_activas)


class GestionarUsuariosUseCase:
    def __init__(self, usuarios: UsuarioRepository, hasher: HasherPort):
        self._usuarios, self._hasher = usuarios, hasher

    def listar(self, actor: Usuario) -> list[Usuario]:
        exigir_rol(actor, Rol.ADMIN)
        return self._usuarios.listar()

    def crear(self, actor: Usuario, ci: str, nombre: str, password: str, rol: Rol,
              telefono: str = "", email: str = "") -> Usuario:
        exigir_rol(actor, Rol.ADMIN)
        ci, nombre = ci.strip(), nombre.strip()
        if not ci or not nombre:
            raise ValidacionError("La cédula y el nombre son obligatorios.")
        if len(password) < 6:
            raise ValidacionError("La contraseña debe tener al menos 6 caracteres.")
        if self._usuarios.obtener_por_ci(ci):
            raise ValidacionError("Ya existe un usuario con esa cédula.")
        u = self._usuarios.guardar(Usuario(ci=ci, nombre=nombre, password_hash=self._hasher.hash(password),
                                           rol=Rol(rol), telefono=telefono.strip(), email=email.strip()))
        log.info("ADMIN %s creó usuario %s (%s)", actor.ci, u.ci, u.rol.value)
        return u

    def actualizar(self, actor: Usuario, usuario_id: int, nombre: Optional[str] = None,
                   rol: Optional[Rol] = None, activo: Optional[bool] = None,
                   password: Optional[str] = None) -> Usuario:
        exigir_rol(actor, Rol.ADMIN)
        u = self._usuarios.obtener(usuario_id)
        if u is None:
            raise NoEncontrado("El usuario no existe.")
        if u.id == actor.id and (activo is False or (rol is not None and Rol(rol) != Rol.ADMIN)):
            raise ReglaNegocio("No puede deshabilitarse ni quitarse el rol de administrador a sí mismo.")
        if nombre is not None and nombre.strip():
            u.nombre = nombre.strip()
        if rol is not None:
            u.rol = Rol(rol)
        if activo is not None:
            u.activo = activo
        if password:
            if len(password) < 6:
                raise ValidacionError("La contraseña debe tener al menos 6 caracteres.")
            u.password_hash = self._hasher.hash(password)
        log.info("ADMIN %s actualizó usuario %s", actor.ci, u.ci)
        return self._usuarios.guardar(u)


class GestionarCategoriasUseCase:
    def __init__(self, categorias: CategoriaRepository):
        self._categorias = categorias

    def crear(self, actor: Usuario, codigo: str, nombre: str) -> Categoria:
        exigir_rol(actor, Rol.ADMIN)
        codigo, nombre = codigo.strip().upper().replace(" ", "_"), nombre.strip()
        if not codigo or not nombre:
            raise ValidacionError("El código y el nombre de la categoría son obligatorios.")
        if self._categorias.obtener_por_codigo(codigo):
            raise ValidacionError("Ya existe una categoría con ese código.")
        c = self._categorias.guardar(Categoria(codigo=codigo, nombre=nombre))
        log.info("ADMIN %s creó categoría %s", actor.ci, codigo)
        return c

    def actualizar(self, actor: Usuario, categoria_id: int, nombre: Optional[str] = None,
                   activa: Optional[bool] = None) -> Categoria:
        exigir_rol(actor, Rol.ADMIN)
        c = self._categorias.obtener(categoria_id)
        if c is None:
            raise NoEncontrado("La categoría no existe.")
        if nombre and nombre.strip():
            c.nombre = nombre.strip()
        if activa is not None:
            c.activa = activa
        log.info("ADMIN %s actualizó categoría %s", actor.ci, c.codigo)
        return self._categorias.guardar(c)

    def eliminar(self, actor: Usuario, categoria_id: int) -> None:
        exigir_rol(actor, Rol.ADMIN)
        if self._categorias.obtener(categoria_id) is None:
            raise NoEncontrado("La categoría no existe.")
        if self._categorias.en_uso(categoria_id):
            raise ReglaNegocio("No se puede eliminar una categoría utilizada en un incidente. Puede desactivarla.")
        self._categorias.eliminar(categoria_id)
        log.info("ADMIN %s eliminó categoría id=%s", actor.ci, categoria_id)
