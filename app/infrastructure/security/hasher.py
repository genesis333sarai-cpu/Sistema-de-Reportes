"""Adaptador de hash de contrasenas con PBKDF2-HMAC-SHA256 (solo libreria estandar)."""
import hashlib
import hmac
import secrets

from app.application.ports import HasherPort


class HasherPBKDF2(HasherPort):
    def __init__(self, iteraciones: int = 200_000):
        self._it = iteraciones

    def hash(self, password: str) -> str:
        sal = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), self._it)
        return f"pbkdf2${self._it}${sal}${dk.hex()}"

    def verificar(self, password: str, hash_guardado: str) -> bool:
        try:
            _, it, sal, esperado = hash_guardado.split("$")
            dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), int(it))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(dk.hex(), esperado)
