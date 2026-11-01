"""Nuevo reporte: RF-01 (registro), RF-02 (categoria), RF-03 (mapa) y RF-04 (fotos)."""
from datetime import datetime, timezone

from nicegui import ui

from app.application.use_cases import RegistrarIncidenteCmd
from app.domain.value_objects import Coordenada, Gravedad, Rol
from app.ui.session import exigir, intentar
from app.ui.theme import marco
from app.domain.rules import validar_imagen

ZONAS = ["Vinto Chico", "Zona Central", "Río Khora", "Combuy"]  # del prototipo; se pueden escribir otras


def registrar(c) -> None:
    @ui.page("/nuevo")
    def nuevo():
        u = exigir(c, Rol.CIUDADANO, Rol.ADMIN)
        if u is None:
            return
        categorias = {x.id: x.nombre for x in c.listar_categorias.ejecutar(solo_activas=True)}
        fotos: list = []
        punto = {"coord": None, "capa": None}
        centro = c.mapa.centro_por_defecto()

        with marco(u, "Nuevo reporte", "Registro de incidente medioambiental"):
            ui.label("Nuevo reporte medioambiental").classes("text-2xl font-bold")
            ui.label("Complete los datos requeridos (*). Los reportes guardados inician en estado «Reportado».").classes("text-grey-7")
            with ui.row().classes("w-full no-wrap gap-4 items-start"):
                with ui.card().classes("flex-1 gap-3"):
                    cat = ui.select(categorias, label="Categoría del incidente *").classes("w-full")
                    ui.label("Gravedad inicial estimada *").classes("text-sm text-grey-8")
                    grav = ui.toggle({int(g): g.etiqueta for g in Gravedad}, value=int(Gravedad.MEDIA))
                    desc = ui.textarea("Descripción del suceso *", placeholder="Describa lo que ocurre y la magnitud del incidente…").classes("w-full").props("rows=4")
                    with ui.row().classes("w-full no-wrap gap-3"):
                        zona = ui.select(ZONAS, label="Zona *", with_input=True, new_value_mode="add-unique").classes("flex-1")
                        direccion = ui.input("Dirección *", placeholder="Ej. Calle Bolívar, altura puente").classes("flex-1")
                    ref = ui.input("Referencia adicional", placeholder="Ej. Al frente de la escuela, casa color verde").classes("w-full")
                    ui.label("Ubicación en el mapa * (haga clic para marcar el punto)").classes("text-sm text-grey-8")
                    mapa = ui.leaflet(center=(centro.latitud, centro.longitud), zoom=14).classes("w-full h-72")
                    etiqueta_coord = ui.label("Aún no marcó ninguna ubicación.").classes("text-xs text-grey-7")

                    def al_clic(e):
                        lat, lng = e.args["latlng"]["lat"], e.args["latlng"]["lng"]
                        ok, coord = intentar(lambda: Coordenada(lat, lng))
                        if not ok:
                            return
                        if punto["capa"] is not None:
                            mapa.remove_layer(punto["capa"])
                        punto["capa"] = mapa.marker(latlng=(lat, lng))
                        punto["coord"] = coord
                        etiqueta_coord.text = f"Ubicación marcada: {lat:.5f}, {lng:.5f}"
                    mapa.on("map-click", al_clic)

                with ui.column().classes("w-96 gap-4"):
                    with ui.card().classes("w-full"):
                        ui.label("Evidencias fotográficas (opcional)").classes("font-bold")

                        def al_subir(e):
                            contenido = e.content.read()
                            ok, _ = intentar(lambda: validar_imagen(e.name, contenido))
                            if not ok:                       # ya mostró el aviso rojo con el motivo
                                return
                            fotos.append((e.name, contenido))
                            ui.notify(f"Foto «{e.name}» cargada correctamente.", type="positive")

                        subida = ui.upload(
                            on_upload=al_subir, multiple=True, auto_upload=True,
                            on_rejected=lambda: ui.notify("Formato no permitido: solo JPG o PNG.", type="negative"),
                            label="Arrastre fotos aquí (JPG o PNG)",
                        ).props('accept=".jpg,.jpeg,.png"').classes("w-full")

                        def quitar():
                            fotos.clear()
                            subida.reset()
                        ui.button("Quitar fotos", icon="delete", on_click=quitar).props("flat dense")
                    with ui.card().classes("w-full gap-1"):
                        ui.label("Datos del reporte (automático)").classes("font-bold")
                        ahora = datetime.now(timezone.utc)
                        for k, v in [("Fecha de registro", ahora.strftime("%d/%m/%Y")), ("Hora de registro", ahora.strftime("%H:%M")), ("Estado inicial", "Reportado")]:
                            with ui.row().classes("w-full justify-between"):
                                ui.label(k).classes("text-grey-7 text-sm")
                                ui.label(v).classes("text-sm font-medium")

                    def enviar():
                        cmd = RegistrarIncidenteCmd(
                            reportante=u, categoria_id=cat.value or 0, descripcion=desc.value or "",
                            gravedad=Gravedad(grav.value), zona=zona.value or "", direccion=direccion.value or "",
                            referencia=ref.value or "", coordenada=punto["coord"], fotos=list(fotos))
                        ok, inc = intentar(lambda: c.registrar_incidente.ejecutar(cmd))
                        if ok:
                            ui.notify(f"Incidente registrado con el código {inc.codigo}.", type="positive", close_button=True, timeout=6000)
                            ui.navigate.to(f"/incidente/{inc.codigo}")

                    ui.button("Registrar incidente oficial", icon="send", on_click=enviar).classes("w-full")
                    ui.button("Cancelar", on_click=lambda: ui.navigate.back()).props("outline").classes("w-full")
