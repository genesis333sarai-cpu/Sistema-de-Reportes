from collections import Counter
from dataclasses import dataclass
from typing import Optional

from app.application.ports import CategoriaRepository, ConsultaIncidentes, FiltroIncidentes
from app.application.use_cases._comun import exigir_rol
from app.domain.entities import Usuario
from app.domain.rules import ESTADOS_ACTIVOS
from app.domain.value_objects import Estado, Gravedad, Rol


@dataclass
class Estadisticas:
    total: int
    criticos_activos: int
    por_categoria: dict
    por_gravedad: dict
    por_estado: dict
    zonas_criticas: list          # [(zona, cantidad)] de mayor a menor
    tiempo_medio_horas: Optional[float]


class ObtenerEstadisticasUseCase:
    """HU-08 / RF-09."""

    def __init__(self, consulta: ConsultaIncidentes, categorias: CategoriaRepository):
        self._consulta, self._categorias = consulta, categorias

    def ejecutar(self, actor: Usuario) -> Estadisticas:
        exigir_rol(actor, Rol.FUNCIONARIO, Rol.ADMIN)
        incs = self._consulta.listar(FiltroIncidentes())
        nombres = {c.id: c.nombre for c in self._categorias.listar()}
        cat = Counter(nombres.get(i.categoria_id, i.categoria_codigo) for i in incs)
        grav = Counter(i.gravedad for i in incs)
        est = Counter(i.estado for i in incs)
        zonas = Counter(i.zona.strip().title() for i in incs)
        tiempos = [(i.fecha_atendido - i.fecha_reporte).total_seconds() / 3600
                   for i in incs if i.fecha_atendido]
        return Estadisticas(
            total=len(incs),
            criticos_activos=sum(1 for i in incs if i.gravedad == Gravedad.CRITICA and i.estado in ESTADOS_ACTIVOS),
            por_categoria=dict(cat.most_common()),
            por_gravedad={g.etiqueta: grav.get(g, 0) for g in Gravedad},
            por_estado={e.value: est.get(e, 0) for e in Estado},
            zonas_criticas=zonas.most_common(5),
            tiempo_medio_horas=round(sum(tiempos) / len(tiempos), 1) if tiempos else None)
