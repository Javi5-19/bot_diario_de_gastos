"""
Funciones auxiliares compartidas por los distintos handlers.
"""

import re

from config import CATEGORIAS, LIMITE_TOKENS


def formatear_numero(numero: int) -> str:
    """Convierte un número a formato con puntos: 2500000 -> 2.500.000"""
    return f"{numero:,}".replace(",", ".")


def contar_tokens(texto: str) -> int:
    """Cuenta aproximadamente los tokens de un mensaje."""
    palabras = len(re.findall(r'\S+', texto))
    return int(palabras * 1.3)


def validar_tokens(texto: str) -> tuple:
    """Verifica si el mensaje excede el límite de tokens."""
    tokens = contar_tokens(texto)
    if tokens > LIMITE_TOKENS:
        return False, tokens
    return True, tokens


def get_emoji_categoria(categoria: str) -> str:
    """Obtiene el emoji de una categoría por su nombre."""
    for cat in CATEGORIAS.values():
        if cat["nombre"] == categoria:
            return cat["emoji"]
    return "💰"


def comandos_rapidos() -> str:
    """Bloque de comandos rápidos básicos (/inicio y /ayuda)."""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/inicio - Ver resumen del mes\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def comandos_con_gasto() -> str:
    """Bloque de comandos incluyendo /gasto para registrar otro."""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/gasto - Registrar otro gasto\n"
        f"/inicio - Ver resumen del mes\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def comandos_con_extra() -> str:
    """Bloque de comandos incluyendo /extra para registrar otro."""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/extra - Registrar otro ingreso extra\n"
        f"/inicio - Ver resumen del mes\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def comandos_inicio() -> str:
    """Bloque de comandos rápidos para /inicio (solo /gasto y /ayuda)."""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/gasto - Registrar un gasto\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )
