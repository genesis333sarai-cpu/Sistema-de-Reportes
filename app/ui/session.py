"""Sesion y control de acceso de la UI (adaptador de entrada). La autorizacion real vive en los casos de uso."""
from typing import Any, Callable, Optional

from nicegui import app, ui

from app.domain.entities import Usuario
from app.domain.errors import DomainError
from app.domain.value_objects import Gravedad, Rol

COLOR_GRAVEDAD = {Gravedad.BAJA: "blue", Gravedad.MEDIA: "amber-8", Gravedad.ALTA: "deep-orange", Gravedad.CRITICA: "red"}
COLOR_ESTADO = {"Reportado": "grey-7", "En revisión": "blue", "En atención": "purple", "Atendido": "green", "Cerrado": "blue-grey-9"}


def inicio_por_rol(rol: Rol) -> str:
    return {Rol.CIUDADANO: "/", Rol.FUNCIONARIO: "/panel", Rol.ADMIN: "/panel", Rol.RESPONSABLE: "/asignaciones"}[rol]


def usuario_actual(c) -> Optional[Usuario]:
    uid = app.storage.user.get("uid")
    return c.obtener_usuario.ejecutar(uid) if uid else None


def exigir(c, *roles: Rol) -> Optional[Usuario]:
    """RF-10: devuelve el usuario si esta autenticado y su rol esta permitido; si no, redirige."""
    u = usuario_actual(c)
    if u is None:
        app.storage.user.pop("uid", None)
        ui.navigate.to("/login")
        return None
    if roles and u.rol not in roles:
        ui.notify("No tiene permiso para acceder a esa sección.", type="negative")
        ui.navigate.to(inicio_por_rol(u.rol))
        return None
    return u


def intentar(accion: Callable[[], Any], ok: Optional[str] = None) -> tuple[bool, Any]:
    """Ejecuta un caso de uso y traduce los errores de negocio a avisos para el usuario."""
    try:
        resultado = accion()
    except DomainError as e:
        ui.notify(str(e), type="negative", multi_line=True)
        return False, None
    if ok:
        ui.notify(ok, type="positive")
    return True, resultado
