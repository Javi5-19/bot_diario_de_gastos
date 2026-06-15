"""
ConversationHandler: registro de un ingreso extra (/extra).
"""

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import LIMITE_PROMPTS_DIA
from database import (
    usuario_existe, obtener_usuario, verificar_limite_prompts,
    guardar_ingreso_extra, total_gastado_mes, total_ingresos_extra_mes,
)
from .helpers import formatear_numero, comandos_rapidos, comandos_con_extra
from .states import EXTRA_MONTO, EXTRA_RAZON, EXTRA_CONFIRMAR
from .registro import inicio_registro


async def inicio_extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de registro de ingreso extra."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 Primero debes registrarte. Escribe /start")
        return ConversationHandler.END

    permitido, _ = await verificar_limite_prompts(chat_id)
    if not permitido:
        await update.message.reply_text(
            f"❌ Llegaste al límite de {LIMITE_PROMPTS_DIA} mensajes por día."
            f"{comandos_rapidos()}"
        )
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "🎉 REGISTRO DE INGRESO EXTRA\n\n"
        "¿Cuál es el MONTO del ingreso extra?\n"
        "(Ejemplo: 500000)"
    )
    return EXTRA_MONTO


async def extra_monto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el monto del ingreso extra."""
    texto = update.message.text.strip()
    texto_limpio = texto.replace(".", "").replace(",", "").replace(" ", "")

    try:
        monto = int(texto_limpio)
        context.user_data["monto_extra"] = monto
        await update.message.reply_text(
            f"Monto: ${formatear_numero(monto)} COP\n\n"
            "📝 ¿Cuál es la RAZÓN de este ingreso extra?\n"
            "(Ejemplo: bono del trabajo, venta de algo, regalo, etc.)"
        )
        return EXTRA_RAZON
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, envía un número válido. Ejemplo: 500000"
        )
        return EXTRA_MONTO


async def extra_razon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la razón del ingreso extra."""
    razon = update.message.text.strip()
    context.user_data["razon_extra"] = razon

    monto = context.user_data["monto_extra"]

    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 REVISA EL INGRESO EXTRA:\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Monto: ${formatear_numero(monto)} COP\n"
        f"📝 Razón: {razon}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"¿Confirmas este ingreso extra?\n"
        f"Responde: SI o NO"
    )
    return EXTRA_CONFIRMAR


async def extra_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma o cancela el ingreso extra."""
    chat_id = update.effective_user.id
    respuesta = update.message.text.strip().upper()

    if respuesta == "SI":
        monto = context.user_data["monto_extra"]
        razon = context.user_data["razon_extra"]

        await guardar_ingreso_extra(chat_id, monto, razon)

        usuario = await obtener_usuario(chat_id)
        total_extra = await total_ingresos_extra_mes(chat_id)
        total_gastado = await total_gastado_mes(chat_id)
        total_disponible = usuario["ingreso_fijo"] + total_extra

        await update.message.reply_text(
            f"✅ INGRESO EXTRA REGISTRADO\n\n"
            f"+ ${formatear_numero(monto)} COP por: {razon}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Total disponible este mes: ${formatear_numero(total_disponible)} COP\n"
            f"💸 Gastado hasta ahora: ${formatear_numero(total_gastado)} COP\n"
            f"💰 Te queda: ${formatear_numero(total_disponible - total_gastado)} COP"
            f"{comandos_con_extra()}"
        )

        context.user_data.clear()
        return ConversationHandler.END

    elif respuesta == "NO":
        await update.message.reply_text(
            f"❌ Ingreso extra cancelado."
            f"{comandos_rapidos()}"
        )
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"Por favor, responde con SI o NO"
            f"{comandos_rapidos()}"
        )
        return EXTRA_CONFIRMAR


extra_handler = ConversationHandler(
    entry_points=[CommandHandler("extra", inicio_extra)],
    states={
        EXTRA_MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_monto)],
        EXTRA_RAZON: [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_razon)],
        EXTRA_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_confirmar)],
    },
    fallbacks=[CommandHandler("start", inicio_registro)],
)
