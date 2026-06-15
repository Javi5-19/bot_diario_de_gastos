#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Punto de entrada de la Libreta de Gastos Bot.

Construye la aplicación de Telegram, registra todos los handlers
y arranca el polling.
"""

from telegram.ext import Application

from config import TOKEN, CONTRASENA, LIMITE_PROMPTS_DIA
from database import crear_tablas
from handlers import get_conversation_handlers, get_command_handlers


async def post_init(application: Application):
    """Se ejecuta antes de empezar a recibir mensajes: prepara la BD."""
    print("🔧 Inicializando base de datos...")
    await crear_tablas()
    print("✅ Base de datos lista.")


def main():
    """Función principal que inicia el bot."""

    print("🚀 Iniciando Libreta de Gastos Bot...")
    print(f"📊 Límite de prompts por día: {LIMITE_PROMPTS_DIA}")
    print(f"🔐 Contraseña configurada: {CONTRASENA}")

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    for handler in get_conversation_handlers():
        app.add_handler(handler)

    for handler in get_command_handlers():
        app.add_handler(handler)

    print("✅ BOT FUNCIONANDO...")
    print("Presiona Ctrl+C para detener el bot")

    app.run_polling()


if __name__ == "__main__":
    main()
