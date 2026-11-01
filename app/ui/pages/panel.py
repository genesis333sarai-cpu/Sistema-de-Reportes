"""Panel municipal (RF-05/09), mis asignaciones del responsable y estadisticas (RF-09)."""
from nicegui import ui

from app.domain.value_objects import Rol
from app.ui.components.tabla_incidentes import tabla_incidentes
from app.ui.session import exigir, intentar
from app.ui.theme import marco

STAFF = (Rol.FUNCIONARIO, Rol.ADMIN)


def _tarjeta(titulo, valor, color="primary"):
    with ui.card().classes("flex-1"):
        ui.label(titulo).classes("text-xs text-grey-7")
        ui.label(str(valor)).classes(f"text-2xl font-bold text-{color}")


def _barras(titulo, datos: dict):
    with ui.card().classes("flex-1 min-w-72 gap-2"):
        ui.label(titulo).classes("font-bold")
        if not datos or not any(datos.values()):
            ui.label("Sin datos todavía.").classes("text-grey-7 text-sm")
            return
        maximo = max(datos.values()) or 1
        for nombre, n in datos.items():
            with ui.row().classes("w-full items-center no-wrap gap-2"):
                ui.label(nombre).classes("w-40 text-sm")
                ui.linear_progress(value=n / maximo, show_value=False, size="12px").classes("flex-1")
                ui.label(str(n)).classes("w-8 text-right text-sm font-medium")


def registrar(c) -> None:
    @ui.page("/panel")
    def panel():
        u = exigir(c, *STAFF)
        if u is None:
            return
        with marco(u, "Panel municipal de monitoreo", "Módulo de fiscalización de incidentes"):
            ui.label("Panel municipal de monitoreo").classes("text-2xl font-bold")
            ok, est = intentar(lambda: c.estadisticas.ejecutar(u))
            if ok:
                with ui.row().classes("w-full gap-4"):
                    _tarjeta("Reportes críticos activos", est.criticos_activos, "negative")
                    _tarjeta("En revisión", est.por_estado["En revisión"], "info")
                    _tarjeta("En atención", est.por_estado["En atención"], "purple")
                    _tarjeta("Atendidos / cerrados", est.por_estado["Atendido"] + est.por_estado["Cerrado"], "positive")
            ui.label("Bandeja de entrada — prioridad crítica primero").classes("text-lg font-bold")
            tabla_incidentes(c, u)

    @ui.page("/asignaciones")
    def asignaciones():
        u = exigir(c, Rol.RESPONSABLE)
        if u is None:
            return
        with marco(u, "Mis asignaciones", "Gestión operativa de incidentes"):
            ui.label("Incidentes asignados a mí").classes("text-2xl font-bold")
            tabla_incidentes(c, u)

    @ui.page("/estadisticas")
    def estadisticas():
        u = exigir(c, *STAFF)
        if u is None:
            return
        with marco(u, "Estadísticas", "Indicadores de incidentes"):
            ui.label("Estadísticas de incidentes").classes("text-2xl font-bold")
            ok, est = intentar(lambda: c.estadisticas.ejecutar(u))
            if not ok:
                return
            with ui.row().classes("w-full gap-4"):
                _tarjeta("Total de incidentes", est.total)
                _tarjeta("Críticos activos", est.criticos_activos, "negative")
                _tarjeta("Tiempo medio de respuesta",
                         "—" if est.tiempo_medio_horas is None else f"{est.tiempo_medio_horas} h", "secondary")
            with ui.row().classes("w-full gap-4"):
                _barras("Por categoría", est.por_categoria)
                _barras("Por gravedad", est.por_gravedad)
            with ui.row().classes("w-full gap-4"):
                _barras("Por estado", est.por_estado)
                _barras("Zonas críticas (más reportes)", dict(est.zonas_criticas))
            ui.label("El tiempo medio de respuesta se calcula desde el reporte hasta que el incidente pasa a «Atendido».").classes("text-xs text-grey-7")
