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
            f" Ya estás registrado como {usuario['nombre']}.\n"
            f"Usa /ayuda para ver los comandos."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        " BIENVENIDO A LIBRETA DE GASTOS\n\n"
        "Este bot es privado. Para usarlo, necesitas la contraseña.\n\n"
        " Escribe la contraseña para continuar:"
    )
    return ESPERANDO_CONTRASENA


async def verificar_contrasena(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica la contraseña escrita por el usuario."""
    texto = update.message.text.strip()

    if texto == CONTRASENA:
        await update.message.reply_text(
            " CONTRASEÑA CORRECTA\n\n"
            "Ahora necesito registrar tus datos.\n\n"
            " ¿Cómo deseas que me dirija a ti?\n"
            "(Ejemplo: Fernan, Javier, etc.)"
        )
        return ESPERANDO_NOMBRE

    await update.message.reply_text(
        " CONTRASEÑA INCORRECTA\n\n"
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
        " ¿Cuál es tu INGRESO MENSUAL FIJO en pesos colombianos?\n"
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
            " Por favor, envía un número válido.\n"
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
            f" ¡REGISTRO COMPLETO!\n\n"
            f"Hola {nombre}.\n"
            f" Ingreso mensual: ${formatear_numero(ingreso)} COP\n\n"
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


"""
ConversationHandler: registro de usuario nuevo (/start).

Flujo:
    /start → contraseña → nombre → ingreso mensual → confirmación → registro completo

Estados:
    ESPERANDO_CONTRASENA  →  ESPERANDO_NOMBRE  →  ESPERANDO_INGRESO  →  CONFIRMANDO_INGRESO


import logging

from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from config import CONTRASENA
from database import usuario_existe, registrar_usuario, obtener_usuario
from .helpers import formatear_numero
from .states import (
    CONFIRMANDO_INGRESO,
    ESPERANDO_CONTRASENA,
    ESPERANDO_INGRESO,
    ESPERANDO_NOMBRE,
)

logger = logging.getLogger(__name__)


# Constantes de respuesta del usuario


RESPUESTA_SI = "SI"
RESPUESTA_NO = "NO"



# Helpers internos


def _limpiar_numero(texto: str) -> int | None:
    
    Convierte un texto con formato numérico colombiano a entero.

    Acepta formatos como: '2.500.000', '2,500,000', '2500000'.
    Retorna None si el texto no es un número válido.
    
    limpio = texto.replace(".", "").replace(",", "").replace(" ", "")
    try:
        valor = int(limpio)
        # Validación de rango mínimo para evitar ingresos absurdos
        return valor if valor > 0 else None
    except ValueError:
        return None



# Paso 1 – Inicio del flujo (/start)


async def inicio_registro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    Punto de entrada del flujo de registro.

    Si el usuario ya existe: muestra un mensaje de bienvenida y termina.
    Si es nuevo:           solicita la contraseña de acceso.
    
    chat_id = update.effective_user.id

    if await usuario_existe(chat_id):
        usuario = await obtener_usuario(chat_id)
        await update.message.reply_text(
            f" Ya estás registrado como *{usuario['nombre']}*.\n"
            "Usa /ayuda para ver los comandos disponibles.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        " *BIENVENIDO A LIBRETA DE GASTOS*\n\n"
        "Este bot es privado. Ingresa la contraseña para continuar:",
        parse_mode="Markdown",
    )
    return ESPERANDO_CONTRASENA



# Paso 2 – Verificación de contraseña


async def verificar_contrasena(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    Compara la contraseña recibida con la almacenada en config.

    Éxito:  avanza al paso de nombre.
    Fallo:  informa al usuario y termina la conversación.
    
    if update.message.text.strip() == CONTRASENA:
        await update.message.reply_text(
            " *Contraseña correcta.*\n\n"
            " ¿Cómo deseas que me dirija a ti?\n"
            "_(Ejemplo: Ana, Javier, Fer…)_",
            parse_mode="Markdown",
        )
        return ESPERANDO_NOMBRE

    logger.warning("Intento fallido de acceso – chat_id: %s", update.effective_user.id)
    await update.message.reply_text(
        " *Contraseña incorrecta.*\n\n"
        "Acceso denegado. Contacta al administrador si crees que es un error.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END



# Paso 3 – Nombre del usuario


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    Guarda el nombre del usuario en user_data y solicita el ingreso mensual.
    
    nombre = update.message.text.strip()

    # Validación básica: evitar nombres vacíos o demasiado largos
    if not nombre or len(nombre) > 50:
        await update.message.reply_text(
            " Por favor escribe un nombre válido (máximo 50 caracteres)."
        )
        return ESPERANDO_NOMBRE

    context.user_data["nombre"] = nombre

    await update.message.reply_text(
        f"Hola, *{nombre}* \n\n"
        " ¿Cuál es tu *ingreso mensual fijo* en pesos colombianos?\n"
        "_(Ejemplo: 2500000 para $2.500.000 COP)_",
        parse_mode="Markdown",
    )
    return ESPERANDO_INGRESO



# Paso 4 – Ingreso mensual


async def recibir_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    Valida el ingreso recibido y solicita confirmación al usuario.

    Si el texto no es un número positivo válido, vuelve a pedir el dato.
   
    ingreso = _limpiar_numero(update.message.text.strip())

    if ingreso is None:
        await update.message.reply_text(
            " Valor inválido. Escribe solo el número sin letras ni símbolos.\n"
            "_(Ejemplo: 2500000)_",
            parse_mode="Markdown",
        )
        return ESPERANDO_INGRESO

    context.user_data["ingreso"] = ingreso

    await update.message.reply_text(
        f"Tu ingreso mensual sería: *${formatear_numero(ingreso)} COP*\n\n"
        "¿Es correcto? Responde *SI* o *NO*.",
        parse_mode="Markdown",
    )
    return CONFIRMANDO_INGRESO



# Paso 5 – Confirmación y registro final


async def confirmar_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    Procesa la respuesta de confirmación del ingreso.

    SI  → registra al usuario en la base de datos y finaliza.
    NO  → regresa al paso de ingreso para corregirlo.
    Otro→ solicita una respuesta válida.
    
    respuesta = update.message.text.strip().upper()
    chat_id = update.effective_user.id

    if respuesta == RESPUESTA_SI:
        nombre = context.user_data["nombre"]
        ingreso = context.user_data["ingreso"]

        await registrar_usuario(chat_id, nombre, ingreso)
        context.user_data.clear()

        logger.info("Usuario registrado – chat_id: %s | nombre: %s", chat_id, nombre)

        await update.message.reply_text(
            " *¡Registro completado!*\n\n"
            f" Nombre: *{nombre}*\n"
            f" Ingreso mensual: *${formatear_numero(ingreso)} COP*\n\n"
            "Usa /ayuda para ver todos los comandos disponibles.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    if respuesta == RESPUESTA_NO:
        await update.message.reply_text(
            "Entendido. Escribe de nuevo tu ingreso mensual:\n"
            "_(Ejemplo: 2500000)_",
            parse_mode="Markdown",
        )
        return ESPERANDO_INGRESO

    # Respuesta no reconocida
    await update.message.reply_text("Por favor responde únicamente *SI* o *NO*.", parse_mode="Markdown")
    return CONFIRMANDO_INGRESO



# Definición del ConversationHandler


registro_handler = ConversationHandler(
    entry_points=[CommandHandler("start", inicio_registro)],
    states={
        ESPERANDO_CONTRASENA:  [MessageHandler(filters.TEXT & ~filters.COMMAND, verificar_contrasena)],
        ESPERANDO_NOMBRE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
        ESPERANDO_INGRESO:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ingreso)],
        CONFIRMANDO_INGRESO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_ingreso)],
    },
    fallbacks=[CommandHandler("start", inicio_registro)],
    # Limpia user_data automáticamente si la conversación expira o se cancela
    conversation_timeout=300,  # 5 minutos de inactividad
)"""
