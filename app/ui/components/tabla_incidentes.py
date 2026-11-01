"""Tabla de incidentes con filtros combinables (RF-05, HU-05). Se reutiliza en varias paginas."""
from datetime import date

from nicegui import ui

from app.application.ports import FiltroIncidentes
from app.domain.value_objects import Estado, Gravedad
from app.ui.session import COLOR_ESTADO, COLOR_GRAVEDAD, intentar

COLUMNAS = [
    {"name": "codigo", "label": "Código", "field": "codigo", "align": "left", "sortable": True},
    {"name": "categoria", "label": "Categoría", "field": "categoria", "align": "left"},
    {"name": "zona", "label": "Zona", "field": "zona", "align": "left", "sortable": True},
    {"name": "fecha", "label": "Fecha", "field": "fecha", "align": "left"},
    {"name": "gravedad", "label": "Gravedad", "field": "gravedad", "align": "left"},
    {"name": "estado", "label": "Estado", "field": "estado", "align": "left"},
]


def _fecha(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def tabla_incidentes(c, usuario, mostrar_filtros: bool = True) -> None:
    nombres = {x.id: x.nombre for x in c.listar_categorias.ejecutar()}
    f = {"cat": None, "grav": None, "est": None, "desde": None, "hasta": None, "zona": ""}
    widgets = []

    @ui.refreshable
    def tabla():
        filtro = FiltroIncidentes(
            categoria_id=f["cat"], gravedad=Gravedad(f["grav"]) if f["grav"] else None,
            estado=Estado(f["est"]) if f["est"] else None, fecha_desde=_fecha(f["desde"]),
            fecha_hasta=_fecha(f["hasta"]), zona=f["zona"] or "")
        ok, incs = intentar(lambda: c.listar_incidentes.ejecutar(usuario, filtro))
        if not ok or not incs:
            with ui.card().classes("w-full items-center p-6"):
                ui.icon("search_off", size="40px", color="grey")
                ui.label("No se encontraron incidentes con los criterios seleccionados.").classes("text-grey-7")
            return
        filas = [{"codigo": i.codigo, "categoria": nombres.get(i.categoria_id, i.categoria_codigo),
                  "zona": i.zona, "fecha": i.fecha_reporte.strftime("%d/%m/%Y %H:%M"),
                  "gravedad": i.gravedad.etiqueta, "gcolor": COLOR_GRAVEDAD[i.gravedad],
                  "estado": i.estado.value, "ecolor": COLOR_ESTADO[i.estado.value]} for i in incs]
        t = ui.table(columns=COLUMNAS, rows=filas, row_key="codigo", pagination=10).classes("w-full cursor-pointer")
        t.add_slot("body-cell-gravedad", '<q-td :props="props"><q-badge :color="props.row.gcolor">{{ props.value }}</q-badge></q-td>')
        t.add_slot("body-cell-estado", '<q-td :props="props"><q-badge outline :color="props.row.ecolor">{{ props.value }}</q-badge></q-td>')
        t.on("rowClick", lambda e: ui.navigate.to(f"/incidente/{e.args[1]['codigo']}"))
        ui.label(f"{len(filas)} incidente(s). Haga clic en una fila para ver el detalle.").classes("text-xs text-grey-7")

    def cambiar(clave):
        def manejador(e):
            f[clave] = e.value
            tabla.refresh()
        return manejador

    def limpiar():
        for w in widgets:
            w.value = None
        f.update({"cat": None, "grav": None, "est": None, "desde": None, "hasta": None, "zona": ""})
        tabla.refresh()

    if mostrar_filtros:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-end gap-3"):
                widgets.append(ui.select(nombres, label="Categoría", clearable=True, on_change=cambiar("cat")).classes("w-48"))
                widgets.append(ui.select({int(g): g.etiqueta for g in Gravedad}, label="Gravedad", clearable=True, on_change=cambiar("grav")).classes("w-32"))
                widgets.append(ui.select({e.value: e.value for e in Estado}, label="Estado", clearable=True, on_change=cambiar("est")).classes("w-40"))
                widgets.append(ui.input("Desde", on_change=cambiar("desde")).props("type=date clearable").classes("w-40"))
                widgets.append(ui.input("Hasta", on_change=cambiar("hasta")).props("type=date clearable").classes("w-40"))
                widgets.append(ui.input("Zona", on_change=cambiar("zona")).props("clearable").classes("w-40"))
                ui.button("Limpiar filtros", icon="filter_alt_off", on_click=limpiar).props("flat")
    tabla()
