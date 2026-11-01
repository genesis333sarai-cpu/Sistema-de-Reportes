"""Pruebas del Principio de Sustitucion de Liskov (LSP).

1) Toda variante de Incidente se comporta como un Incidente.
2) Toda implementacion de IncidenteRepository cumple el mismo contrato.
"""
import os
import tempfile

import pytest

from app.domain.entities import Incidente
from app.domain.factories import IncidenteFactory
from app.domain.value_objects import Coordenada, Estado, Gravedad
from tests.fakes import IncidenteRepoMem


def _nuevo(codigo_categoria: str) -> Incidente:
    return IncidenteFactory.crear(
        codigo_categoria, categoria_id=1, descripcion="Descripción suficientemente larga",
        gravedad=Gravedad.ALTA, zona="Vinto Chico", direccion="Calle Bolívar",
        referencia="Junto al río", coordenada=Coordenada(-17.39, -66.32), reportante_id=1)


def test_toda_variante_se_comporta_como_incidente():
    codigos = list(IncidenteFactory._registro) + ["CATEGORIA_SIN_VARIANTE"]
    resultados = set()
    for codigo in codigos:
        inc = _nuevo(codigo)
        assert isinstance(inc, Incidente)            # se puede usar donde se espera un Incidente
        inc.agregar_observacion("Fabio", "Nota", publica=True)
        inc.asignar(7, "Raúl", "Fabio")
        inc.cambiar_estado(Estado.EN_REVISION, "Fabio")
        inc.cambiar_estado(Estado.EN_ATENCION, "Fabio")
        inc.cambiar_estado(Estado.ATENDIDO, "Raúl")
        # mismo comportamiento observable en todas las variantes
        resultados.add((inc.estado, len(inc.historial), len(inc.observaciones), inc.responsable_id,
                        inc.fecha_atendido is not None))
    assert len(resultados) == 1, f"Alguna variante se comporta distinto: {resultados}"


def contrato_incidente_repository(repo) -> None:
    """Lo que CUALQUIER implementacion de IncidenteRepository debe cumplir."""
    inc = _nuevo("BASURA")
    inc.codigo = "VIN-2026-001"
    guardado = repo.guardar(inc)
    assert guardado.id is not None
    leido = repo.obtener_por_codigo("VIN-2026-001")
    assert leido.codigo == "VIN-2026-001" and leido.gravedad == Gravedad.ALTA
    assert leido.coordenada == Coordenada(-17.39, -66.32)
    assert repo.obtener_por_codigo("NO-EXISTE") is None
    assert repo.siguiente_numero(2026) == 2
    leido.cambiar_estado(Estado.EN_REVISION, "Fabio")
    repo.guardar(leido)                                   # actualizar no duplica
    assert repo.obtener_por_codigo("VIN-2026-001").estado == Estado.EN_REVISION
    assert repo.siguiente_numero(2026) == 2


def test_repositorio_en_memoria_cumple_el_contrato():
    contrato_incidente_repository(IncidenteRepoMem())


def test_repositorio_sqlmodel_cumple_el_mismo_contrato():
    pytest.importorskip("sqlmodel")                       # se ejecuta donde SQLModel esta instalado
    from app.infrastructure.persistence.repositories import IncidenteRepositorySQL, crear_engine
    with tempfile.TemporaryDirectory() as carpeta:
        engine = crear_engine(f"sqlite:///{os.path.join(carpeta, 'contrato.db')}")
        contrato_incidente_repository(IncidenteRepositorySQL(engine))
        engine.dispose()
