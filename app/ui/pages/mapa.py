"""RF-08: mapa interactivo (OpenStreetMap/Leaflet) con un marcador por incidente."""
from nicegui import ui

from app.ui.session import COLOR_GRAVEDAD, exigir, intentar
from app.ui.theme import marco


def dibujar_marcadores(mapa, marcadores) -> None:
    for m in marcadores:
        capa = mapa.generic_layer(name="circleMarker", args=[
            (m.coordenada.latitud, m.coordenada.longitud),
            {"color": m.color, "fillColor": m.color, "fillOpacity": 0.7, "radius": 10}])
        try:
            capa.run_method("bindPopup", m.detalle)
        except Exception:  # el popup es solo un extra visual
            pass


def registrar(c) -> None:
    @ui.page("/mapa")
    def mapa_page():
        u = exigir(c)
        if u is None:
            return
        with marco(u, "Mapa de incidentes", "Visualización geográfica", ancho="max-w-7xl"):
            ui.label("Mapa de incidentes").classes("text-2xl font-bold")
            ok, incs = intentar(lambda: c.listar_incidentes.ejecutar(u))
            incs = incs or []
            marcadores = c.mapa.marcadores(incs)
            with ui.row().classes("items-center gap-4"):
                for nombre, color in [("Baja", "#2E86DE"), ("Media", "#F5B041"), ("Alta", "#E67E22"), ("Crítica", "#C0392B")]:
                    with ui.row().classes("items-center gap-1"):
                        ui.element("div").style(f"width:14px;height:14px;border-radius:50%;background:{color}")
                        ui.label(nombre).classes("text-sm")
                ui.label(f"{len(marcadores)} incidente(s) con ubicación").classes("text-sm text-grey-7")
            centro = c.mapa.centro_por_defecto()
            m = ui.leaflet(center=(centro.latitud, centro.longitud), zoom=14).classes("w-full h-[70vh]")
            dibujar_marcadores(m, marcadores)
            if not marcadores:
                ui.label("Todavía no hay incidentes para mostrar.").classes("text-grey-7")
