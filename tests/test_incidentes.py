from datetime import datetime, timedelta

import pytest

from app.application.ports import FiltroIncidentes
from app.application.use_cases import (
    AgregarObservacionUseCase, AsignarResponsableUseCase, CambiarEstadoUseCase,
    ClasificarIncidenteUseCase, ListarIncidentesUseCase, ObtenerIncidenteUseCase,
    RegistrarIncidenteCmd, RegistrarIncidenteUseCase)
from app.domain.entities import Incidente
from app.domain.factories import IncidenteFactory
from app.domain.errors import NoEncontrado, PermisoDenegado, TransicionInvalida, ValidacionError
from app.domain.value_objects import Coordenada, Estado, Gravedad, Rol
from tests.fakes import Mundo

JPG = b"\xff\xd8\xff\xe0" + b"0" * 50
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50


def registrar(m: Mundo, categoria=None, gravedad=Gravedad.MEDIA, fotos=None, usuario=None, **extra):
    cat = categoria or m.cat_basura
    datos = dict(reportante=usuario or m.ciudadano, categoria_id=cat.id,
                 descripcion="Acumulación de basura en la esquina", gravedad=gravedad,
                 zona="Vinto Chico", direccion="Calle Bolívar", referencia="Frente a la escuela",
                 coordenada=Coordenada(-17.39, -66.32), fotos=fotos or [])
    datos.update(extra)
    return RegistrarIncidenteUseCase(m.incidentes, m.categorias, m.almacen).ejecutar(RegistrarIncidenteCmd(**datos))


# ---------- RF-01 / RF-02 / RF-03 / RF-04: registro ----------
def test_registro_genera_codigo_estado_y_fecha():
    m = Mundo()
    inc = registrar(m)
    assert inc.codigo == f"VIN-{datetime.now().year}-001"
    assert inc.estado == Estado.REPORTADO
    assert inc.fecha_reporte <= datetime.now()
    assert inc.historial[0].estado_nuevo == "Reportado"
    assert registrar(m).codigo.endswith("-002")


def test_registro_con_fotos_validas_y_sin_fotos():
    m = Mundo()
    con = registrar(m, fotos=[("a.jpg", JPG), ("b.PNG", PNG)])
    assert len(con.evidencias) == 2 and len(m.almacen.archivos) == 2
    assert registrar(m).evidencias == []          # fotos opcionales


def test_formato_de_imagen_invalido_no_guarda_nada():
    m = Mundo()
    for nombre, datos in [("virus.exe", JPG), ("falsa.jpg", b"no soy imagen"), ("vacia.png", b"")]:
        with pytest.raises(ValidacionError):
            registrar(m, fotos=[(nombre, datos)])
    assert m.incidentes.d == {} and m.almacen.archivos == {}


def test_campos_obligatorios():
    m = Mundo()
    with pytest.raises(ValidacionError):
        registrar(m, descripcion="corta")
    with pytest.raises(ValidacionError):
        registrar(m, zona="  ")
    with pytest.raises(ValidacionError):
        registrar(m, coordenada=None)
    with pytest.raises(ValidacionError):
        registrar(m, categoria_id=999)


def test_coordenada_fuera_de_rango():
    with pytest.raises(ValidacionError):
        Coordenada(95, 0)
    with pytest.raises(ValidacionError):
        Coordenada(0, 181)


def test_factory_aplica_reglas_por_categoria():
    m = Mundo()
    with pytest.raises(ValidacionError):
        registrar(m, categoria=m.cat_quema, gravedad=Gravedad.BAJA)
    registrar(m, categoria=m.cat_quema, gravedad=Gravedad.ALTA)
    with pytest.raises(ValidacionError):
        registrar(m, categoria=m.cat_agua, referencia="")


# ---------- RF-05: consulta, filtros y prioridad ----------
def test_criticos_primero_y_filtros():
    m = Mundo()
    baja = registrar(m, gravedad=Gravedad.BAJA)
    critica = registrar(m, gravedad=Gravedad.CRITICA, zona="Combuy")
    alta = registrar(m, gravedad=Gravedad.ALTA, categoria=m.cat_quema)
    listar = ListarIncidentesUseCase(m.incidentes)
    orden = [i.codigo for i in listar.ejecutar(m.funcionario)]
    assert orden == [critica.codigo, alta.codigo, baja.codigo]
    assert [i.codigo for i in listar.ejecutar(m.funcionario, FiltroIncidentes(zona="comb"))] == [critica.codigo]
    assert [i.codigo for i in listar.ejecutar(m.funcionario, FiltroIncidentes(categoria_id=m.cat_quema.id))] == [alta.codigo]
    assert len(listar.ejecutar(m.funcionario, FiltroIncidentes(gravedad=Gravedad.CRITICA, estado=Estado.REPORTADO))) == 1
    assert listar.ejecutar(m.funcionario, FiltroIncidentes(estado=Estado.CERRADO)) == []
    ayer = (datetime.now() - timedelta(days=1)).date()
    assert listar.ejecutar(m.funcionario, FiltroIncidentes(fecha_hasta=ayer)) == []


def test_ciudadano_solo_ve_los_suyos():
    m = Mundo()
    mio = registrar(m)
    ajeno = registrar(m, usuario=m.otro)
    assert [i.codigo for i in ListarIncidentesUseCase(m.incidentes).ejecutar(m.ciudadano)] == [mio.codigo]
    obtener = ObtenerIncidenteUseCase(m.incidentes)
    assert obtener.ejecutar(m.ciudadano, mio.codigo).codigo == mio.codigo
    with pytest.raises(NoEncontrado):
        obtener.ejecutar(m.ciudadano, ajeno.codigo)


# ---------- HU-04: clasificar ----------
def test_funcionario_modifica_gravedad_y_queda_en_historial():
    m = Mundo()
    inc = registrar(m)
    out = ClasificarIncidenteUseCase(m.incidentes, m.categorias).ejecutar(
        m.funcionario, inc.codigo, Gravedad.CRITICA, motivo="Riesgo para la salud")
    assert out.gravedad == Gravedad.CRITICA
    assert out.historial[-1].accion == "Cambio de gravedad"
    with pytest.raises(PermisoDenegado):
        ClasificarIncidenteUseCase(m.incidentes, m.categorias).ejecutar(m.ciudadano, inc.codigo, Gravedad.BAJA)


def test_clasificar_cambia_categoria_con_reglas_de_la_nueva():
    m = Mundo()
    inc = registrar(m, gravedad=Gravedad.BAJA)
    uc = ClasificarIncidenteUseCase(m.incidentes, m.categorias)
    with pytest.raises(ValidacionError):            # Quema no admite gravedad baja
        uc.ejecutar(m.funcionario, inc.codigo, Gravedad.BAJA, categoria_id=m.cat_quema.id)
    out = uc.ejecutar(m.funcionario, inc.codigo, Gravedad.ALTA, categoria_id=m.cat_quema.id)
    assert out.categoria_id == m.cat_quema.id and out.categoria_codigo == "QUEMA"


# ---------- RF-06 / RF-07: estados y asignacion ----------
def test_flujo_completo_de_estados():
    m = Mundo()
    inc = registrar(m)
    AsignarResponsableUseCase(m.incidentes, m.usuarios).ejecutar(m.funcionario, inc.codigo, m.responsable.id)
    cambiar = CambiarEstadoUseCase(m.incidentes)
    estado = m.incidentes.obtener_por_codigo(inc.codigo)
    assert estado.estado == Estado.EN_ATENCION and estado.responsable_id == m.responsable.id
    cambiar.ejecutar(m.responsable, inc.codigo, Estado.ATENDIDO, "Se limpió la zona")
    final = cambiar.ejecutar(m.funcionario, inc.codigo, Estado.CERRADO)
    assert final.estado == Estado.CERRADO and final.fecha_atendido is not None
    pasos = [(h.estado_anterior, h.estado_nuevo) for h in final.historial if h.accion == "Cambio de estado"]
    assert pasos == [("Reportado", "En revisión"), ("En revisión", "En atención"),
                     ("En atención", "Atendido"), ("Atendido", "Cerrado")]


def test_transiciones_invalidas():
    m = Mundo()
    inc = registrar(m)
    cambiar = CambiarEstadoUseCase(m.incidentes)
    with pytest.raises(TransicionInvalida):
        cambiar.ejecutar(m.funcionario, inc.codigo, Estado.CERRADO)      # no se cierra sin atender
    with pytest.raises(TransicionInvalida):
        cambiar.ejecutar(m.funcionario, inc.codigo, Estado.ATENDIDO)     # no se salta pasos


def test_permisos_de_estado_y_asignacion():
    m = Mundo()
    inc = registrar(m)
    asignar = AsignarResponsableUseCase(m.incidentes, m.usuarios)
    with pytest.raises(PermisoDenegado):
        asignar.ejecutar(m.ciudadano, inc.codigo, m.responsable.id)
    with pytest.raises(ValidacionError):                                 # un ciudadano no es responsable
        asignar.ejecutar(m.funcionario, inc.codigo, m.ciudadano.id)
    r = m.usuarios.obtener(m.otro_resp.id); r.activo = False; m.usuarios.guardar(r)
    with pytest.raises(ValidacionError):                                 # responsable inactivo
        asignar.ejecutar(m.funcionario, inc.codigo, m.otro_resp.id)
    asignar.ejecutar(m.funcionario, inc.codigo, m.responsable.id)
    cambiar = CambiarEstadoUseCase(m.incidentes)
    with pytest.raises(PermisoDenegado):                                 # responsable NO asignado
        cambiar.ejecutar(m.otro_resp, inc.codigo, Estado.ATENDIDO)
    with pytest.raises(PermisoDenegado):                                 # ciudadano
        cambiar.ejecutar(m.ciudadano, inc.codigo, Estado.ATENDIDO)


def test_responsable_solo_lista_sus_asignaciones():
    m = Mundo()
    a, b = registrar(m), registrar(m)
    AsignarResponsableUseCase(m.incidentes, m.usuarios).ejecutar(m.funcionario, a.codigo, m.responsable.id)
    ls = ListarIncidentesUseCase(m.incidentes).ejecutar(m.responsable)
    assert [i.codigo for i in ls] == [a.codigo]


def test_observaciones_publicas_y_privadas():
    m = Mundo()
    inc = registrar(m)
    uc = AgregarObservacionUseCase(m.incidentes)
    uc.ejecutar(m.funcionario, inc.codigo, "Nota interna", publica=False)
    out = uc.ejecutar(m.funcionario, inc.codigo, "Estamos revisando su reporte", publica=True)
    assert len(out.observaciones_para(Rol.FUNCIONARIO)) == 2
    assert [o.texto for o in out.observaciones_para(Rol.CIUDADANO)] == ["Estamos revisando su reporte"]
    with pytest.raises(ValidacionError):
        uc.ejecutar(m.funcionario, inc.codigo, "   ")
    with pytest.raises(PermisoDenegado):
        uc.ejecutar(m.ciudadano, inc.codigo, "intento")


def test_no_se_inicia_atencion_sin_responsable():
    m = Mundo()
    inc = registrar(m)
    cambiar = CambiarEstadoUseCase(m.incidentes)
    cambiar.ejecutar(m.funcionario, inc.codigo, Estado.EN_REVISION)
    with pytest.raises(ValidacionError):
        cambiar.ejecutar(m.funcionario, inc.codigo, Estado.EN_ATENCION)


def test_lsp_toda_variante_se_usa_como_incidente():
    """LSP: el codigo que recibe un Incidente funciona igual con cualquier variante."""
    for codigo in ("BASURA", "QUEMA", "TALA", "AGUA", "AIRE", "AREAS_VERDES", "CATEGORIA_NUEVA"):
        inc = IncidenteFactory.crear(
            codigo, categoria_id=1, descripcion="Descripción suficiente del incidente",
            gravedad=Gravedad.ALTA, zona="Combuy", direccion="Calle 1", referencia="Río Khora",
            coordenada=Coordenada(-17.39, -66.32), reportante_id=1)
        assert isinstance(inc, Incidente)
        inc.cambiar_estado(Estado.EN_REVISION, "funcionario")
        inc.cambiar_gravedad(Gravedad.CRITICA, "funcionario", "riesgo")
        assert inc.estado == Estado.EN_REVISION and inc.gravedad == Gravedad.CRITICA
        with pytest.raises(ValidacionError):      # mismo tipo de error en todas las variantes
            inc.descripcion = "corta"
            inc.validar()
