"""Patron Adapter: traduce MapaPort (interfaz propia) a datos para OpenStreetMap/Leaflet."""
from app.application.ports import Marcador, MapaPort
from app.domain.entities import Incidente
from app.domain.value_objects import Coordenada, Gravedad

COLORES = {
    Gravedad.BAJA: "#2E86DE",
    Gravedad.MEDIA: "#F5B041",
    Gravedad.ALTA: "#E67E22",
    Gravedad.CRITICA: "#C0392B",
}


class OpenStreetMapAdapter(MapaPort):
    # Aproximado para el centro de Vinto (Cochabamba): verificar con el mapa real.
    CENTRO_VINTO = Coordenada(latitud=-17.39, longitud=-66.32)

    def centro_por_defecto(self) -> Coordenada:
        return self.CENTRO_VINTO

    def marcadores(self, incidentes: list[Incidente]) -> list[Marcador]:
        return [
            Marcador(i.coordenada, i.codigo,
                     f"{i.codigo} · {i.gravedad.etiqueta} · {i.estado.value} · {i.zona}",
                     COLORES[i.gravedad])
            for i in incidentes if i.coordenada
        ]
