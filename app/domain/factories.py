"""Patron Factory: crea la variante de Incidente segun la categoria (RF-02).

Para soportar una categoria nueva con reglas propias basta crear una clase y
registrarla con @IncidenteFactory.registrar(...). No se modifica codigo existente (OCP).
"""
from app.domain.entities import Incidente
from app.domain.errors import ValidacionError
from app.domain.value_objects import Gravedad


class IncidenteFactory:
    _registro: dict[str, type] = {}

    @classmethod
    def registrar(cls, codigo: str):
        def deco(clase):
            cls._registro[codigo.upper()] = clase
            return clase
        return deco

    @classmethod
    def _clase(cls, codigo: str) -> type:
        return cls._registro.get(codigo.upper(), Incidente)

    @classmethod
    def crear(cls, codigo_categoria: str, **datos) -> Incidente:
        """Crea y valida un incidente nuevo."""
        incidente = cls._clase(codigo_categoria)(categoria_codigo=codigo_categoria.upper(), **datos)
        incidente.validar()
        return incidente

    @classmethod
    def reconstruir(cls, codigo_categoria: str, **datos) -> Incidente:
        """Rehidrata un incidente guardado (sin volver a validar)."""
        return cls._clase(codigo_categoria)(categoria_codigo=codigo_categoria.upper(), **datos)


@IncidenteFactory.registrar("QUEMA")
class IncidenteQuema(Incidente):
    def validar(self) -> None:
        super().validar()
        if self.gravedad < Gravedad.MEDIA:
            raise ValidacionError("Una quema de residuos no puede clasificarse con gravedad baja.")


@IncidenteFactory.registrar("TALA")
class IncidenteTala(Incidente):
    def validar(self) -> None:
        super().validar()
        if self.gravedad < Gravedad.MEDIA:
            raise ValidacionError("La tala de árboles debe tener gravedad media o superior.")


@IncidenteFactory.registrar("AGUA")
class IncidenteAgua(Incidente):
    def validar(self) -> None:
        super().validar()
        if not self.referencia.strip():
            raise ValidacionError("Para contaminación de agua indique una referencia del lugar (río, canal, etc.).")


@IncidenteFactory.registrar("AIRE")
class IncidenteAire(Incidente):
    pass


@IncidenteFactory.registrar("BASURA")
class IncidenteBasura(Incidente):
    pass


@IncidenteFactory.registrar("AREAS_VERDES")
class IncidenteAreasVerdes(Incidente):
    pass
