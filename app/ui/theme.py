"""Marco comun de las paginas: encabezado y menu lateral segun el rol (RF-10)."""
from nicegui import app, ui

from app.domain.entities import Usuario
from app.domain.value_objects import Rol

MENUS = {
    Rol.CIUDADANO: [("home", "Inicio ciudadano", "/"), ("add_circle", "Nuevo reporte", "/nuevo"), ("map", "Mapa", "/mapa")],
    Rol.FUNCIONARIO: [("dashboard", "Panel de monitoreo", "/panel"), ("map", "Mapa", "/mapa"), ("bar_chart", "Estadísticas", "/estadisticas")],
    Rol.RESPONSABLE: [("assignment", "Mis asignaciones", "/asignaciones"), ("map", "Mapa", "/mapa")],
    Rol.ADMIN: [("dashboard", "Panel de monitoreo", "/panel"), ("map", "Mapa", "/mapa"), ("bar_chart", "Estadísticas", "/estadisticas"),
                ("add_circle", "Nuevo reporte", "/nuevo"), ("settings", "Configuración y roles", "/admin")],
}


def marco(usuario: Usuario, titulo: str, subtitulo: str = "", ancho: str = "max-w-6xl"):
    """Dibuja encabezado + menu y devuelve la columna donde va el contenido."""
    ui.colors(primary="#1F4E3D", secondary="#2E6B52", accent="#8BC34A")
    with ui.header().classes("items-center justify-between bg-primary text-white"):
        with ui.row().classes("items-center gap-3"):
            ui.icon("eco", size="28px")
            with ui.column().classes("gap-0"):
                ui.label("G.A.M. Vinto — Incidentes Medioambientales").classes("text-base font-bold")
                ui.label(subtitulo or titulo).classes("text-xs opacity-80")
        with ui.row().classes("items-center gap-3"):
            with ui.column().classes("gap-0 items-end"):
                ui.label(usuario.nombre).classes("text-sm font-medium")
                ui.label(usuario.rol.value).classes("text-xs opacity-80")
            ui.button(icon="logout", on_click=lambda: ui.navigate.to("/logout")).props("flat round color=white").tooltip("Cerrar sesión")
    with ui.left_drawer(bordered=True).classes("bg-green-1"):
        ui.label("SISTEMA DE REPORTES").classes("text-xs text-grey-7 font-bold")
        ui.label("Ambiente Vinto").classes("text-lg font-bold text-primary mb-2")
        for icono, texto, ruta in MENUS[usuario.rol]:
            ui.button(texto, icon=icono, on_click=lambda r=ruta: ui.navigate.to(r)).props("flat align=left no-caps").classes("w-full")
        ui.separator().classes("my-3")
        ui.label("Línea de emergencia").classes("text-xs text-grey-7")
        ui.label("800-14-0202").classes("font-bold")  # dato del prototipo
    return ui.column().classes(f"w-full {ancho} mx-auto p-4 gap-4")
