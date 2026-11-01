import pytest

from app.application.use_cases import (
    AutenticarUseCase, GestionarCategoriasUseCase, GestionarUsuariosUseCase,
    ObtenerEstadisticasUseCase, RegistrarCiudadanoUseCase, AsignarResponsableUseCase, CambiarEstadoUseCase)
from app.domain.errors import PermisoDenegado, ReglaNegocio, ValidacionError
from app.domain.value_objects import Gravedad, Rol
from tests.fakes import Mundo
from tests.test_incidentes import registrar


# ---------- RF-10: autenticacion y roles ----------
def test_login_correcto_e_incorrecto():
    m = Mundo()
    auth = AutenticarUseCase(m.usuarios, m.hasher)
    assert auth.ejecutar("111", "secreto1").nombre == "Ana Ciudadana"
    for ci, pw in [("111", "mala"), ("999", "secreto1")]:
        with pytest.raises(ValidacionError):
            auth.ejecutar(ci, pw)


def test_cuenta_deshabilitada_no_ingresa():
    m = Mundo()
    GestionarUsuariosUseCase(m.usuarios, m.hasher).actualizar(m.admin, m.ciudadano.id, activo=False)
    with pytest.raises(ValidacionError):
        AutenticarUseCase(m.usuarios, m.hasher).ejecutar("111", "secreto1")


def test_registro_de_ciudadano():
    m = Mundo()
    reg = RegistrarCiudadanoUseCase(m.usuarios, m.hasher)
    u = reg.ejecutar("555", "Nuevo Vecino", "clave123")
    assert u.rol == Rol.CIUDADANO and u.password_hash != "clave123"
    with pytest.raises(ValidacionError):
        reg.ejecutar("555", "Duplicado", "clave123")
    with pytest.raises(ValidacionError):
        reg.ejecutar("556", "Clave corta", "123")


def test_solo_admin_gestiona_usuarios_y_categorias():
    m = Mundo()
    usuarios = GestionarUsuariosUseCase(m.usuarios, m.hasher)
    cats = GestionarCategoriasUseCase(m.categorias)
    for actor in (m.ciudadano, m.funcionario, m.responsable):
        with pytest.raises(PermisoDenegado):
            usuarios.crear(actor, "900", "X", "clave123", Rol.ADMIN)
        with pytest.raises(PermisoDenegado):
            cats.crear(actor, "NUEVA", "Nueva")
    u = usuarios.crear(m.admin, "900", "Nuevo Funcionario", "clave123", Rol.FUNCIONARIO)
    assert u.rol == Rol.FUNCIONARIO


def test_admin_no_puede_deshabilitarse_a_si_mismo():
    m = Mundo()
    with pytest.raises(ReglaNegocio):
        GestionarUsuariosUseCase(m.usuarios, m.hasher).actualizar(m.admin, m.admin.id, activo=False)


# ---------- HU-09 / RF-02: categorias ----------
def test_categoria_en_uso_no_se_elimina_pero_si_se_desactiva():
    m = Mundo()
    cats = GestionarCategoriasUseCase(m.categorias)
    nueva = cats.crear(m.admin, "desborde aguas", "Desborde de aguas servidas")
    assert nueva.codigo == "DESBORDE_AGUAS"
    cats.eliminar(m.admin, nueva.id)                       # sin uso: se puede
    assert m.categorias.obtener(nueva.id) is None
    m.categorias.usadas.add(m.cat_basura.id)
    with pytest.raises(ReglaNegocio):
        cats.eliminar(m.admin, m.cat_basura.id)
    assert cats.actualizar(m.admin, m.cat_basura.id, activa=False).activa is False
    with pytest.raises(ValidacionError):                   # categoria inactiva no admite reportes
        registrar(m, categoria=m.categorias.obtener(m.cat_basura.id))
    with pytest.raises(ValidacionError):
        cats.crear(m.admin, "BASURA", "Duplicada")


# ---------- RF-09: estadisticas ----------
def test_estadisticas():
    m = Mundo()
    a = registrar(m, gravedad=Gravedad.CRITICA, zona="Vinto Chico")
    registrar(m, gravedad=Gravedad.BAJA, zona="vinto chico")
    registrar(m, gravedad=Gravedad.ALTA, categoria=m.cat_quema, zona="Combuy")
    AsignarResponsableUseCase(m.incidentes, m.usuarios).ejecutar(m.funcionario, a.codigo, m.responsable.id)
    CambiarEstadoUseCase(m.incidentes).ejecutar(m.responsable, a.codigo, "Atendido")
    est = ObtenerEstadisticasUseCase(m.incidentes, m.categorias).ejecutar(m.funcionario)
    assert est.total == 3
    assert est.por_categoria == {"Basura": 2, "Quema": 1}
    assert est.por_gravedad == {"Baja": 1, "Media": 0, "Alta": 1, "Critica": 1}
    assert est.por_estado["Atendido"] == 1 and est.por_estado["Reportado"] == 2
    assert est.zonas_criticas[0] == ("Vinto Chico", 2)
    assert est.criticos_activos == 0                 # el critico ya fue atendido
    assert est.tiempo_medio_horas is not None and est.tiempo_medio_horas >= 0
    with pytest.raises(PermisoDenegado):
        ObtenerEstadisticasUseCase(m.incidentes, m.categorias).ejecutar(m.ciudadano)
