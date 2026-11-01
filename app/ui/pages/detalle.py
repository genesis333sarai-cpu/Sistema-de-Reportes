"""Detalle del incidente: estado (RF-06), responsable (RF-07), clasificacion, evidencias e historial."""
from nicegui import ui

from app.application.use_cases import CambiarEstadoUseCase
from app.domain.errors import DomainError
from app.domain.rules import TRANSICIONES
from app.domain.value_objects import Estado, Gravedad, Rol
from app.ui.pages.mapa import dibujar_marcadores
from app.ui.session import COLOR_ESTADO, COLOR_GRAVEDAD, exigir, inicio_por_rol, intentar
from app.ui.theme import marco

STAFF = (Rol.FUNCIONARIO, Rol.ADMIN)


def registrar(c) -> None:
    @ui.page("/incidente/{codigo}")
    def detalle(codigo: str):
        u = exigir(c)
        if u is None:
            return
        ok, inc = intentar(lambda: c.obtener_incidente.ejecutar(u, codigo))
        if not ok:
            ui.navigate.to(inicio_por_rol(u.rol))
            return
        nombres = {x.id: x.nombre for x in c.listar_categorias.ejecutar()}
        puede_actuar = CambiarEstadoUseCase.puede_actuar(u, inc)
        es_staff = u.rol in STAFF
        recargar = ui.navigate.reload

        with marco(u, f"Incidente {inc.codigo}", "Detalle y gestión de incidente"):
            with ui.row().classes("items-center gap-3"):
                ui.label(f"Incidente: {inc.codigo}").classes("text-2xl font-bold")
                ui.badge(inc.gravedad.etiqueta, color=COLOR_GRAVEDAD[inc.gravedad])
                ui.badge(inc.estado.value, color=COLOR_ESTADO[inc.estado.value])
                ui.space()
                ui.button("Volver", icon="arrow_back", on_click=lambda: ui.navigate.to(inicio_por_rol(u.rol))).props("outline")

            # ---- barra de estados + accion ----
            with ui.card().classes("w-full gap-2"):
                ui.label("Estado del incidente").classes("text-xs text-grey-7 font-bold")
                with ui.row().classes("w-full gap-2"):
                    for e in Estado:
                        actual = e == inc.estado
                        ui.badge(e.value, color="primary" if actual else "grey-4").props("" if actual else "text-color=grey-8").classes("px-4 py-2 text-sm")
                siguientes = sorted(TRANSICIONES[inc.estado], key=lambda s: list(Estado).index(s))
                if puede_actuar and siguientes:
                    obs = ui.input("Observación del cambio (opcional)").classes("w-full")
                    with ui.row():
                        for s in siguientes:
                            def cambiar(s=s):
                                ok2, _ = intentar(lambda: c.cambiar_estado.ejecutar(u, inc.codigo, s, obs.value or ""),
                                                  f"Estado actualizado a «{s.value}».")
                                if ok2:
                                    recargar()
                            ui.button(f"Pasar a «{s.value}»", on_click=cambiar)
                elif not siguientes:
                    ui.label("El incidente está cerrado.").classes("text-sm text-grey-7")

            with ui.row().classes("w-full no-wrap gap-4 items-start"):
                with ui.column().classes("flex-1 gap-4"):
                    with ui.card().classes("w-full gap-2"):
                        ui.label("Datos del reporte").classes("font-bold")
                        for k, v in [("Categoría", nombres.get(inc.categoria_id, inc.categoria_codigo)),
                                     ("Fecha", inc.fecha_reporte.strftime("%d/%m/%Y %H:%M")),
                                     ("Zona", inc.zona), ("Dirección", inc.direccion), ("Referencia", inc.referencia or "—")]:
                            with ui.row().classes("w-full justify-between"):
                                ui.label(k).classes("text-grey-7 text-sm")
                                ui.label(v).classes("text-sm font-medium")
                        ui.label("Descripción").classes("text-grey-7 text-sm mt-2")
                        ui.label(inc.descripcion)
                    with ui.card().classes("w-full gap-2"):
                        ui.label("Evidencia visual adjunta").classes("font-bold")
                        if inc.evidencias:
                            with ui.row().classes("gap-3"):
                                for ruta in inc.evidencias:
                                    ui.image(f"/uploads/{ruta}").classes("w-56 rounded")
                        else:
                            ui.label("Este reporte no incluye fotografías.").classes("text-grey-7 text-sm")
                    if inc.coordenada:
                        with ui.card().classes("w-full gap-2"):
                            ui.label("Ubicación").classes("font-bold")
                            mp = ui.leaflet(center=(inc.coordenada.latitud, inc.coordenada.longitud), zoom=16).classes("w-full h-64")
                            dibujar_marcadores(mp, c.mapa.marcadores([inc]))
                            ui.label(f"{inc.coordenada.latitud:.5f}, {inc.coordenada.longitud:.5f}").classes("text-xs text-grey-7")

                with ui.column().classes("w-96 gap-4"):
                    if es_staff:
                        with ui.card().classes("w-full gap-2"):
                            ui.label("Responsable de atención").classes("font-bold")
                            resp = {r.id: r.nombre for r in c.listar_responsables.ejecutar()}
                            sel = ui.select(resp, label="Asignar técnico responsable", value=inc.responsable_id if inc.responsable_id in resp else None).classes("w-full")

                            def asignar():
                                if not sel.value:
                                    ui.notify("Seleccione un responsable.", type="warning")
                                    return
                                ok2, _ = intentar(lambda: c.asignar.ejecutar(u, inc.codigo, sel.value), "Responsable asignado.")
                                if ok2:
                                    recargar()
                            ui.button("Guardar asignación", on_click=asignar).classes("w-full")
                        with ui.card().classes("w-full gap-2"):
                            ui.label("Clasificación y prioridad").classes("font-bold")
                            cats = {x.id: x.nombre for x in c.listar_categorias.ejecutar(solo_activas=True)}
                            if inc.categoria_id not in cats:
                                cats[inc.categoria_id] = nombres.get(inc.categoria_id, inc.categoria_codigo)
                            scat = ui.select(cats, label="Categoría", value=inc.categoria_id).classes("w-full")
                            sgrav = ui.select({int(g): g.etiqueta for g in Gravedad}, label="Gravedad", value=int(inc.gravedad)).classes("w-full")
                            motivo = ui.input("Motivo del cambio").classes("w-full")

                            def clasificar():
                                ok2, _ = intentar(lambda: c.clasificar.ejecutar(u, inc.codigo, Gravedad(sgrav.value), scat.value, motivo.value or ""),
                                                  "Clasificación actualizada.")
                                if ok2:
                                    recargar()
                            ui.button("Guardar clasificación", on_click=clasificar).classes("w-full")
                    with ui.card().classes("w-full gap-2"):
                        ui.label("Historial de auditoría").classes("font-bold")
                        for h in reversed(inc.historial):
                            with ui.column().classes("gap-0 w-full"):
                                ui.label(f"{h.accion} — {h.usuario}").classes("text-sm font-medium")
                                if h.estado_nuevo:
                                    ui.label(f"{h.estado_anterior or '—'} → {h.estado_nuevo}").classes("text-xs")
                                if h.observacion:
                                    ui.label(h.observacion).classes("text-xs text-grey-8")
                                ui.label(h.fecha.strftime("%d/%m/%Y %H:%M")).classes("text-xs text-grey-6")
                            ui.separator()
                    with ui.card().classes("w-full gap-2"):
                        ui.label("Observaciones" if u.rol == Rol.CIUDADANO else "Observaciones del funcionario").classes("font-bold")
                        visibles = inc.observaciones_para(u.rol)
                        if not visibles:
                            ui.label("Sin observaciones.").classes("text-grey-7 text-sm")
                        for o in visibles:
                            with ui.column().classes("gap-0"):
                                ui.label(o.texto).classes("text-sm")
                                ui.label(f"{o.autor} · {o.fecha.strftime('%d/%m/%Y %H:%M')}" + ("" if o.publica else " · interna")).classes("text-xs text-grey-6")
                        if puede_actuar:
                            txt = ui.textarea("Escriba comentarios de seguimiento…").classes("w-full").props("rows=2")
                            pub = ui.checkbox("Visible para el ciudadano")

                            def agregar():
                                ok2, _ = intentar(lambda: c.observacion.ejecutar(u, inc.codigo, txt.value or "", bool(pub.value)),
                                                  "Observación registrada.")
                                if ok2:
                                    recargar()
                            ui.button("Agregar comentario", on_click=agregar).props("outline").classes("w-full")
