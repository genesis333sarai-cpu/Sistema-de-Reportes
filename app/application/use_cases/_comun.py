from app.domain.entities import Usuario
from app.domain.errors import PermisoDenegado
from app.domain.value_objects import Rol


def exigir_rol(actor: Usuario, *roles: Rol) -> None:
    """Control de acceso por rol a nivel de caso de uso (RF-10, RNF-03)."""
    if actor is None or not actor.activo or actor.rol not in roles:
        raise PermisoDenegado("Su rol no tiene permiso para realizar esta acción.")
