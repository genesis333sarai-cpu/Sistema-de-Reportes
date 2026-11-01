from app.ui.pages import acceso, admin, detalle, mapa, panel, reporte


def registrar_paginas(c) -> None:
    for modulo in (acceso, reporte, panel, detalle, mapa, admin):
        modulo.registrar(c)
