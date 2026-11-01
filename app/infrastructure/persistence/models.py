"""Modelos SQLModel (tablas). Son detalles de infraestructura: el dominio no los conoce."""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class UsuarioDB(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: Optional[int] = Field(default=None, primary_key=True)
    ci: str = Field(index=True, unique=True)
    nombre: str
    password_hash: str
    rol: str
    activo: bool = True
    telefono: str = ""
    email: str = ""


class CategoriaDB(SQLModel, table=True):
    __tablename__ = "categorias"
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)
    nombre: str
    activa: bool = True


class IncidenteDB(SQLModel, table=True):
    __tablename__ = "incidentes"
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)
    categoria_id: int = Field(index=True)
    categoria_codigo: str
    descripcion: str
    gravedad: int = Field(index=True)
    estado: str = Field(index=True)
    zona: str = Field(index=True)
    direccion: str
    referencia: str = ""
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    reportante_id: int = Field(index=True)
    responsable_id: Optional[int] = Field(default=None, index=True)
    fecha_reporte: datetime = Field(index=True)
    fecha_atendido: Optional[datetime] = None
    # Colecciones que siempre se leen junto al incidente: se guardan como JSON (MVP).
    evidencias: list = Field(default_factory=list, sa_column=Column(JSON))
    historial: list = Field(default_factory=list, sa_column=Column(JSON))
    observaciones: list = Field(default_factory=list, sa_column=Column(JSON))
