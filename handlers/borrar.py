"""
ConversationHandler: borrado total de los datos del usuario
(/borrar_todo o /reset). Requiere doble confirmación + contraseña. 
"""

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import CONTRASENA
from database import usuario_existe, borrar_todos_datos_usuario
from .helpers import comandos_rapidos
from .states import BORRAR_CONFIRMAR1, BORRAR_CONTRASENA, BORRAR_CONFIRMAR2
from .consultas import inicio


async def borrar_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso para borrar todos los datos del usuario."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 No estás registrado. No hay datos para borrar.")
        return ConversationHandler.END

    await update.message.reply_text(
        "⚠️ ¡ADVERTENCIA! ⚠️\n\n"
        "Este comando BORRARÁ TODOS tus datos:\n"
        "• Gastos registrados\n"
        "• Ingresos extra\n"
        "• Historial de meses\n"
        "• Tu nombre e ingreso fijo\n\n"
        "Esta acción NO se puede deshacer.\n\n"
        "¿Estás SEGURO?\n"
        "Responde: SI o NO"
    )
    return BORRAR_CONFIRMAR1


async def borrar_confirmar1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Primera confirmación de borrado."""
    respuesta = update.message.text.strip().upper()

    if respuesta == "SI":
        await update.message.reply_text(
            "🔐 Para confirmar, escribe la CONTRASEÑA:"
        )
        return BORRAR_CONTRASENA
    elif respuesta == "NO":
        await update.message.reply_text(
            f"❌ Operación cancelada. Tus datos están seguros."
            f"{comandos_rapidos()}"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Por favor, responde con SI o NO"
        )
        return BORRAR_CONFIRMAR1


async def borrar_contrasena(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica la contraseña."""
    contrasena_ingresada = update.message.text.strip()

    if contrasena_ingresada == CONTRASENA:
        await update.message.reply_text(
            "🔄 ÚLTIMA CONFIRMACIÓN\n\n"
            "Para borrar TODOS tus datos, escribe:\n"
            "BORRAR MIS DATOS"
        )
        return BORRAR_CONFIRMAR2

    await update.message.reply_text(
        f"❌ Contraseña incorrecta. Operación cancelada."
        f"{comandos_rapidos()}"
    )
    return ConversationHandler.END


async def borrar_confirmar2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Segunda confirmación de borrado con texto específico."""
    respuesta = update.message.text.strip()
    chat_id = update.effective_user.id

    if respuesta == "BORRAR MIS DATOS":
        await borrar_todos_datos_usuario(chat_id)

        await update.message.reply_text(
            "✅ TODOS TUS DATOS HAN SIDO ELIMINADOS\n\n"
            "• Gastos: Eliminados\n"
            "• Ingresos extra: Eliminados\n"
            "• Historial: Eliminado\n"
            "• Perfil: Eliminado\n\n"
            "Puedes volver a registrarte con /start cuando quieras.\n\n"
            "¡Hasta pronto! 👋"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"❌ Confirmación incorrecta. Operación cancelada.\n\n"
        f"Tus datos están seguros."
        f"{comandos_rapidos()}"
    )
    return ConversationHandler.END


borrar_handler = ConversationHandler(
    entry_points=[
        CommandHandler("borrar_todo", borrar_todo),
        CommandHandler("reset", borrar_todo),
    ],
    states={
        BORRAR_CONFIRMAR1: [MessageHandler(filters.TEXT & ~filters.COMMAND, borrar_confirmar1)],
        BORRAR_CONTRASENA: [MessageHandler(filters.TEXT & ~filters.COMMAND, borrar_contrasena)],
        BORRAR_CONFIRMAR2: [MessageHandler(filters.TEXT & ~filters.COMMAND, borrar_confirmar2)],
    },
    fallbacks=[CommandHandler("inicio", inicio)],
)
