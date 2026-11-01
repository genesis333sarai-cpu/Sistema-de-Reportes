"""Errores del dominio. La UI los traduce a mensajes para el usuario."""


class DomainError(Exception):
    """Base de todos los errores de negocio."""


class ValidacionError(DomainError):
    """Datos obligatorios ausentes o con formato invalido (RNF-05)."""


class TransicionInvalida(DomainError):
    """Cambio de estado no permitido por el flujo."""


class PermisoDenegado(DomainError):
    """El rol del usuario no permite la accion (RBAC)."""


class NoEncontrado(DomainError):
    """El recurso solicitado no existe."""


class ReglaNegocio(DomainError):
    """Se viola una regla del negocio (por ejemplo, eliminar una categoria en uso)."""
