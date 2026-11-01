from app.application.ports import HasherPort, UsuarioRepository
from app.domain.entities import Usuario
from app.domain.errors import ValidacionError
from app.domain.value_objects import Rol


class AutenticarUseCase:
    def __init__(self, usuarios: UsuarioRepository, hasher: HasherPort):
        self._usuarios, self._hasher = usuarios, hasher

    def ejecutar(self, ci: str, password: str) -> Usuario:
        usuario = self._usuarios.obtener_por_ci(ci.strip())
        # mismo mensaje para todos los fallos: no revela si la cuenta existe
        if not usuario or not usuario.activo or not self._hasher.verificar(password, usuario.password_hash):
            raise ValidacionError("Cédula o contraseña incorrecta, o cuenta deshabilitada.")
        return usuario


class RegistrarCiudadanoUseCase:
    def __init__(self, usuarios: UsuarioRepository, hasher: HasherPort):
        self._usuarios, self._hasher = usuarios, hasher

    def ejecutar(self, ci: str, nombre: str, password: str, telefono: str = "", email: str = "") -> Usuario:
        ci, nombre = ci.strip(), nombre.strip()
        if not ci or not nombre:
            raise ValidacionError("La cédula y el nombre son obligatorios.")
        if len(password) < 6:
            raise ValidacionError("La contraseña debe tener al menos 6 caracteres.")
        if self._usuarios.obtener_por_ci(ci):
            raise ValidacionError("Ya existe una cuenta con esa cédula de identidad.")
        return self._usuarios.guardar(Usuario(
            ci=ci, nombre=nombre, password_hash=self._hasher.hash(password),
            rol=Rol.CIUDADANO, telefono=telefono.strip(), email=email.strip()))


class ObtenerUsuarioActivoUseCase:
    """Recupera al usuario de la sesion; si fue deshabilitado, la sesion deja de ser valida."""

    def __init__(self, usuarios: UsuarioRepository):
        self._usuarios = usuarios

    def ejecutar(self, usuario_id: int):
        u = self._usuarios.obtener(usuario_id)
        return u if u and u.activo else None
