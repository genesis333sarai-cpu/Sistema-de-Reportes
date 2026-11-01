"""Login, registro de ciudadanos, cierre de sesion e inicio del ciudadano (RF-10)."""
from nicegui import app, ui

from app.domain.value_objects import Rol
from app.ui.components.tabla_incidentes import tabla_incidentes
from app.ui.session import exigir, inicio_por_rol, intentar, usuario_actual
from app.ui.theme import marco


def registrar(c) -> None:
    @ui.page("/login")
    def login():
        ui.colors(primary="#1F4E3D")
        u = usuario_actual(c)
        if u:
            ui.navigate.to(inicio_por_rol(u.rol))
            return

        def entrar():
            ok, usuario = intentar(lambda: c.autenticar.ejecutar(ci.value or "", pw.value or ""))
            if ok:
                app.storage.user["uid"] = usuario.id
                ui.navigate.to(inicio_por_rol(usuario.rol))

        def abrir_registro():
            with ui.dialog() as d, ui.card().classes("w-96"):
                ui.label("Registrar cuenta ciudadana").classes("text-lg font-bold")
                rci = ui.input("Cédula de identidad (CI) *").classes("w-full")
                rn = ui.input("Nombre completo *").classes("w-full")
                rt = ui.input("Teléfono (opcional)").classes("w-full")
                re_ = ui.input("Correo (opcional)").classes("w-full")
                rp = ui.input("Contraseña * (mín. 6 caracteres)", password=True, password_toggle_button=True).classes("w-full")

                def guardar():
                    ok, _ = intentar(lambda: c.registrar_ciudadano.ejecutar(rci.value or "", rn.value or "", rp.value or "", rt.value or "", re_.value or ""),
                                     "Cuenta creada. Ya puede ingresar.")
                    if ok:
                        ci.value = rci.value
                        d.close()
                with ui.row().classes("w-full justify-end"):
                    ui.button("Cancelar", on_click=d.close).props("flat")
                    ui.button("Registrarme", on_click=guardar)
            d.open()

        with ui.row().classes("w-full min-h-screen no-wrap"):
            with ui.column().classes("w-1/2 bg-primary text-white p-12 justify-between gap-4 hidden md:flex"):
                ui.label("MUNICIPIO DE VINTO").classes("text-xs tracking-widest opacity-80")
                ui.label("Portal de Incidentes Medioambientales").classes("text-3xl font-bold")
                ui.space()
                ui.label("Protegemos la salud de nuestros valles, ríos y comunidades de forma transparente e inmediata.").classes("text-lg")
                ui.label("Reporte quema de basura, contaminación de canales de riego, tala ilegal y más.").classes("text-sm opacity-80")
            with ui.column().classes("flex-1 items-center justify-center p-8"):
                with ui.card().classes("w-96 gap-3"):
                    ui.label("Ingreso al Portal").classes("text-xl font-bold")
                    ui.label("Inicie sesión para registrar y dar seguimiento a sus reportes.").classes("text-xs text-grey-7")
                    ci = ui.input("Cédula de identidad (CI)").classes("w-full")
                    pw = ui.input("Contraseña de acceso", password=True, password_toggle_button=True).classes("w-full").on("keydown.enter", entrar)
                    ui.button("Ingresar al sistema", on_click=entrar).classes("w-full")
                    ui.button("Registrar nueva cuenta ciudadana", on_click=abrir_registro).props("outline").classes("w-full")

    @ui.page("/logout")
    def logout():
        app.storage.user.clear()
        ui.navigate.to("/login")

    @ui.page("/")
    def inicio():
        u = exigir(c)
        if u is None:
            return
        if u.rol != Rol.CIUDADANO:
            ui.navigate.to(inicio_por_rol(u.rol))
            return
        with marco(u, "Inicio ciudadano", "Gestión de Reportes y Fiscalización de Vinto"):
            ui.label(f"¡Bienvenido, {u.nombre.split()[0]}!").classes("text-2xl font-bold")
            ui.label("Siga el estado de sus reportes medioambientales presentados al municipio.").classes("text-grey-7")
            ui.button("Crear nuevo reporte", icon="add", on_click=lambda: ui.navigate.to("/nuevo"))
            ok, mios = intentar(lambda: c.listar_incidentes.ejecutar(u))
            mios = mios or []
            with ui.row().classes("w-full gap-4"):
                for icono, valor, texto in [
                    ("description", len(mios), "Mis reportes totales"),
                    ("pending_actions", sum(1 for i in mios if i.estado.value in ("En revisión", "En atención")), "En atención / revisión"),
                    ("check_circle", sum(1 for i in mios if i.estado.value in ("Atendido", "Cerrado")), "Resueltos / atendidos")]:
                    with ui.card().classes("flex-1 flex-row items-center gap-3"):
                        ui.icon(icono, size="32px", color="primary")
                        with ui.column().classes("gap-0"):
                            ui.label(str(valor)).classes("text-2xl font-bold")
                            ui.label(texto).classes("text-xs text-grey-7")
            ui.label("Historial de mis reportes enviados").classes("text-lg font-bold")
            tabla_incidentes(c, u)
