"""
Paquete handlers: toda la lógica de conversación e interacción con
Telegram, organizada por funcionalidad.
"""

from telegram.ext import CommandHandler

from .registro import registro_handler
from .gasto import gasto_handler
from .extra import extra_handler
from .perfil import nombre_handler, cambiar_ingreso
from .borrar import borrar_handler
from .consultas import mes_handler, inicio, lista_gastos, deshacer, ayuda


def get_conversation_handlers():
    """ConversationHandlers (flujos paso a paso de varios mensajes)."""
    return [
        registro_handler,
        gasto_handler,
        extra_handler,
        mes_handler,
        nombre_handler,
        borrar_handler,
    ]


def get_command_handlers():
    """Comandos simples de una sola respuesta."""
    return [
        CommandHandler("inicio", inicio),
        CommandHandler("lista", lista_gastos),
        CommandHandler("ingreso", cambiar_ingreso),
        CommandHandler("deshacer", deshacer),
        CommandHandler("ayuda", ayuda),
    ]
