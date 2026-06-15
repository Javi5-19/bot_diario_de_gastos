"""
Edición de perfil: cambiar nombre (/cambiar_nombre, conversación)
y cambiar ingreso fijo (/ingreso [monto]).
"""

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from database import usuario_existe, obtener_usuario, actualizar_nombre_usuario, actualizar_ingreso_fijo
from .helpers import formatear_numero, comandos_rapidos
from .states import NOMBRE_NUEVO, CONFIRMAR_NOMBRE


# ----------------------------------------------------------------------
# Cambiar nombre (/cambiar_nombre)
# ----------------------------------------------------------------------

async def cambiar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso para cambiar el nombre del usuario."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 Primero debes registrarte. Escribe /start")
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 CAMBIAR NOMBRE\n\n"
        "¿Cuál es tu NUEVO nombre?\n"
        "(Ejemplo: Lorena, Javier, etc.)"
    )
    return NOMBRE_NUEVO


async def recibir_nuevo_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el nuevo nombre y pide confirmación."""
    nuevo_nombre = update.message.text.strip()
    context.user_data["nuevo_nombre"] = nuevo_nombre
    usuario = await obtener_usuario(update.effective_user.id)

    await update.message.reply_text(
        f"Confirmas que tu nuevo nombre es '{nuevo_nombre}'?\n\n"
        f"Nombre anterior: {usuario['nombre']}\n\n"
        f"Responde: SI o NO"
    )
    return CONFIRMAR_NOMBRE


async def confirmar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma o cancela el cambio de nombre."""
    chat_id = update.effective_user.id
    respuesta = update.message.text.strip().upper()

    if respuesta == "SI":
        nuevo_nombre = context.user_data["nuevo_nombre"]
        usuario = await obtener_usuario(chat_id)
        nombre_anterior = usuario["nombre"]

        await actualizar_nombre_usuario(chat_id, nuevo_nombre)

        await update.message.reply_text(
            f"✅ NOMBRE ACTUALIZADO\n\n"
            f"💰 Antes: {nombre_anterior}\n"
            f"💰 Ahora: {nuevo_nombre}"
            f"{comandos_rapidos()}"
        )
        context.user_data.clear()
        return ConversationHandler.END

    elif respuesta == "NO":
        await update.message.reply_text(
            f"❌ Cambio de nombre cancelado."
            f"{comandos_rapidos()}"
        )
        context.user_data.clear()
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            f"Por favor, responde con SI o NO"
            f"{comandos_rapidos()}"
        )
        return CONFIRMAR_NOMBRE


# El fallback "/inicio" se importa aquí para evitar un ciclo de imports
# con consultas.py (que a su vez no depende de este módulo).
from .consultas import inicio  # noqa: E402

nombre_handler = ConversationHandler(
    entry_points=[CommandHandler("cambiar_nombre", cambiar_nombre)],
    states={
        NOMBRE_NUEVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nuevo_nombre)],
        CONFIRMAR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_nombre)],
    },
    fallbacks=[CommandHandler("inicio", inicio)],
)


# ----------------------------------------------------------------------
# Cambiar ingreso fijo (/ingreso [monto])
# ----------------------------------------------------------------------

async def cambiar_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cambia el ingreso fijo mensual."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 Primero debes registrarte. Escribe /start")
        return

    if not context.args:
        await update.message.reply_text(
            f"💰 Para cambiar tu ingreso fijo:\n"
            f"/ingreso [nuevo_monto]\n\n"
            f"Ejemplo: /ingreso 3000000"
            f"{comandos_rapidos()}"
        )
        return

    try:
        texto = " ".join(context.args)
        texto_limpio = texto.replace(".", "").replace(",", "").replace(" ", "")
        nuevo_ingreso = int(texto_limpio)

        usuario = await obtener_usuario(chat_id)
        ingreso_anterior = usuario["ingreso_fijo"]

        await actualizar_ingreso_fijo(chat_id, nuevo_ingreso)

        await update.message.reply_text(
            f"✅ INGRESO FIJO ACTUALIZADO\n\n"
            f"💰 Antes: ${formatear_numero(ingreso_anterior)} COP\n"
            f"💰 Ahora: ${formatear_numero(nuevo_ingreso)} COP"
            f"{comandos_rapidos()}"
        )
    except ValueError:
        await update.message.reply_text(
            f"❌ Por favor, envía un número válido.\n"
            f"Ejemplo: /ingreso 3000000"
            f"{comandos_rapidos()}"
        )
