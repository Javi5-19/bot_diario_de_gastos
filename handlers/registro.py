"""
ConversationHandler: registro de usuario nuevo (/start).

Pide la contraseña, el nombre y el ingreso mensual fijo.
"""

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import CONTRASENA
from database import usuario_existe, registrar_usuario, obtener_usuario
from .helpers import formatear_numero
from .states import ESPERANDO_CONTRASENA, ESPERANDO_NOMBRE, ESPERANDO_INGRESO, CONFIRMANDO_INGRESO


async def inicio_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de registro (primera vez)."""
    chat_id = update.effective_user.id

    if await usuario_existe(chat_id):
        usuario = await obtener_usuario(chat_id)
        await update.message.reply_text(
            f"✅ Ya estás registrado como {usuario['nombre']}.\n"
            f"Usa /ayuda para ver los comandos."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🔐 BIENVENIDO A LIBRETA DE GASTOS\n\n"
        "Este bot es privado. Para usarlo, necesitas la contraseña.\n\n"
        "📝 Escribe la contraseña para continuar:"
    )
    return ESPERANDO_CONTRASENA


async def verificar_contrasena(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica la contraseña escrita por el usuario."""
    texto = update.message.text.strip()

    if texto == CONTRASENA:
        await update.message.reply_text(
            "✅ CONTRASEÑA CORRECTA\n\n"
            "Ahora necesito registrar tus datos.\n\n"
            "📝 ¿Cómo deseas que me dirija a ti?\n"
            "(Ejemplo: Fernan, Javier, etc.)"
        )
        return ESPERANDO_NOMBRE

    await update.message.reply_text(
        "❌ CONTRASEÑA INCORRECTA\n\n"
        "La contraseña no es válida. El bot se detendrá para ti.\n"
        "Si crees que es un error, contacta al administrador."
    )
    return ConversationHandler.END


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el nombre del usuario."""
    nombre = update.message.text.strip()
    context.user_data["nombre"] = nombre

    await update.message.reply_text(
        f"Gracias {nombre}.\n\n"
        "💰 ¿Cuál es tu INGRESO MENSUAL FIJO en pesos colombianos?\n"
        "(Ejemplo: 2500000 para dos millones quinientos mil pesos)"
    )
    return ESPERANDO_INGRESO


async def recibir_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el ingreso mensual y pide confirmación."""
    texto = update.message.text.strip()
    texto_limpio = texto.replace(".", "").replace(",", "").replace(" ", "")

    try:
        ingreso = int(texto_limpio)
        context.user_data["ingreso"] = ingreso

        await update.message.reply_text(
            f"Confirmaste ingreso de ${formatear_numero(ingreso)} COP.\n\n"
            f"¿Es correcto?\n"
            f"Responde: SI o NO"
        )
        return CONFIRMANDO_INGRESO
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, envía un número válido.\n"
            "Ejemplo: 2500000"
        )
        return ESPERANDO_INGRESO


async def confirmar_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma o rechaza el ingreso mensual."""
    respuesta = update.message.text.strip().upper()
    chat_id = update.effective_user.id

    if respuesta == "SI":
        nombre = context.user_data["nombre"]
        ingreso = context.user_data["ingreso"]

        await registrar_usuario(chat_id, nombre, ingreso)

        await update.message.reply_text(
            f"✅ ¡REGISTRO COMPLETO!\n\n"
            f"Hola {nombre}.\n"
            f"💰 Ingreso mensual: ${formatear_numero(ingreso)} COP\n\n"
            f"Ya puedes usar todos los comandos.\n"
            f"Usa /ayuda para ver la lista."
        )

        context.user_data.clear()
        return ConversationHandler.END

    elif respuesta == "NO":
        await update.message.reply_text(
            "Ok, vuelve a escribir tu ingreso mensual:\n"
            "(Ejemplo: 2500000)"
        )
        return ESPERANDO_INGRESO

    else:
        await update.message.reply_text("Por favor, responde con SI o NO")
        return CONFIRMANDO_INGRESO


registro_handler = ConversationHandler(
    entry_points=[CommandHandler("start", inicio_registro)],
    states={
        ESPERANDO_CONTRASENA: [MessageHandler(filters.TEXT & ~filters.COMMAND, verificar_contrasena)],
        ESPERANDO_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
        ESPERANDO_INGRESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ingreso)],
        CONFIRMANDO_INGRESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_ingreso)],
    },
    fallbacks=[CommandHandler("start", inicio_registro)],
)
