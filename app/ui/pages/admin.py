"""RF-10 / HU-09: administracion de usuarios, roles y categorias."""
from nicegui import ui

from app.domain.value_objects import Rol
from app.ui.session import exigir, intentar
from app.ui.theme import marco


def registrar(c) -> None:
    @ui.page("/admin")
    def admin():
        u = exigir(c, Rol.ADMIN)
        if u is None:
            return
        with marco(u, "Configuración general del sistema", "Panel de control del sistema"):
            ui.label("Configuración general del sistema").classes("text-2xl font-bold")
            ui.label("Gestione cuentas, asigne roles y configure las categorías del catálogo ambiental.").classes("text-grey-7")
            with ui.row().classes("w-full no-wrap gap-4 items-start"):
                _usuarios(c, u)
                _categorias(c, u)


def _usuarios(c, admin) -> None:
    @ui.refreshable
    def lista():
        ok, us = intentar(lambda: c.usuarios.listar(admin))
        for x in us or []:
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-0"):
                    ui.label(x.nombre).classes("font-medium")
                    ui.label(f"CI {x.ci} · {x.rol.value}").classes("text-xs text-grey-7")
                with ui.row().classes("items-center"):
                    ui.badge("Activo" if x.activo else "Inactivo", color="positive" if x.activo else "grey")
                    ui.button(icon="edit", on_click=lambda x=x: dialogo(x)).props("flat round dense")
            ui.separator()

    def dialogo(x=None):
        with ui.dialog() as d, ui.card().classes("w-96"):
            ui.label("Nuevo usuario" if x is None else f"Editar: {x.nombre}").classes("text-lg font-bold")
            ci = ui.input("Cédula de identidad *", value=x.ci if x else "").classes("w-full")
            if x:
                ci.props("readonly")
            nom = ui.input("Nombre completo *", value=x.nombre if x else "").classes("w-full")
            rol = ui.select({r.value: r.value for r in Rol}, label="Rol", value=(x.rol if x else Rol.FUNCIONARIO).value).classes("w-full")
            pw = ui.input("Contraseña" + (" (dejar vacío para no cambiar)" if x else " *"), password=True, password_toggle_button=True).classes("w-full")
            activo = ui.switch("Cuenta activa", value=x.activo if x else True)

            def guardar():
                if x is None:
                    ok, _ = intentar(lambda: c.usuarios.crear(admin, ci.value or "", nom.value or "", pw.value or "", Rol(rol.value)), "Usuario creado.")
                else:
                    ok, _ = intentar(lambda: c.usuarios.actualizar(admin, x.id, nom.value, Rol(rol.value), activo.value, pw.value or None), "Usuario actualizado.")
                if ok:
                    d.close()
                    lista.refresh()
            with ui.row().classes("w-full justify-end"):
                ui.button("Cancelar", on_click=d.close).props("flat")
                ui.button("Guardar", on_click=guardar)
        d.open()

    with ui.card().classes("flex-1 gap-2"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Control de usuarios y roles").classes("font-bold")
            ui.button("Nuevo usuario", icon="add", on_click=lambda: dialogo()).props("dense")
        lista()


def _categorias(c, admin) -> None:
    @ui.refreshable
    def lista():
        for cat in c.listar_categorias.ejecutar():
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-0"):
                    ui.label(cat.nombre).classes("font-medium")
                    ui.label(cat.codigo).classes("text-xs text-grey-7")
                with ui.row().classes("items-center"):
                    def alternar(e, cat=cat):
                        intentar(lambda: c.categorias.actualizar(admin, cat.id, activa=e.value))
                    ui.switch("Activa", value=cat.activa, on_change=alternar)

                    def eliminar(cat=cat):
                        ok, _ = intentar(lambda: c.categorias.eliminar(admin, cat.id), "Categoría eliminada.")
                        if ok:
                            lista.refresh()
                    ui.button(icon="delete", on_click=eliminar).props("flat round dense color=negative")
            ui.separator()

    def crear():
        with ui.dialog() as d, ui.card().classes("w-96"):
            ui.label("Nueva categoría").classes("text-lg font-bold")
            cod = ui.input("Código * (ej. DESBORDE_AGUAS)").classes("w-full")
            nom = ui.input("Nombre *").classes("w-full")

            def guardar():
                ok, _ = intentar(lambda: c.categorias.crear(admin, cod.value or "", nom.value or ""), "Categoría creada.")
                if ok:
                    d.close()
                    lista.refresh()
            with ui.row().classes("w-full justify-end"):
                ui.button("Cancelar", on_click=d.close).props("flat")
                ui.button("Guardar", on_click=guardar)
        d.open()

    with ui.card().classes("flex-1 gap-2"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Catálogo de categorías").classes("font-bold")
            ui.button("Crear nueva", icon="add", on_click=crear).props("dense")
        ui.label("Regla del sistema: no se puede eliminar una categoría ya utilizada en un incidente; desactívela en su lugar.").classes("text-xs text-orange-9 bg-orange-1 p-2 rounded")
        lista()
