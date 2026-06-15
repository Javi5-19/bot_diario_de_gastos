"""
ConversationHandler: registro de un gasto (/gasto).

Pide monto, descripción, categoría y confirmación. Incluye alerta
si el gasto supera el 50% del ingreso mensual.
"""

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import CATEGORIAS, LIMITE_PROMPTS_DIA
from database import (
    usuario_existe, obtener_usuario, verificar_limite_prompts,
    guardar_gasto, total_gastado_mes, total_ingresos_extra_mes,
)
from .helpers import formatear_numero, get_emoji_categoria, comandos_rapidos, comandos_con_gasto
from .states import GASTO_MONTO, GASTO_DESCRIPCION, GASTO_CATEGORIA, GASTO_CONFIRMAR


async def inicio_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de registro de gasto."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 Primero debes registrarte. Escribe /start")
        return ConversationHandler.END

    permitido, restantes = await verificar_limite_prompts(chat_id)
    if not permitido:
        await update.message.reply_text(
            f"❌ Llegaste al límite de {LIMITE_PROMPTS_DIA} mensajes por día.\n"
            f"Te quedan {restantes} mensajes para mañana."
            f"{comandos_rapidos()}"
        )
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "💰 REGISTRO DE GASTO\n\n"
        "¿Cuál es el MONTO del gasto?\n"
        "(Solo números, sin puntos ni comas. Ejemplo: 15000)"
    )
    return GASTO_MONTO


async def gasto_monto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el monto del gasto."""
    texto = update.message.text.strip()
    texto_limpio = texto.replace(".", "").replace(",", "").replace(" ", "")

    try:
        monto = int(texto_limpio)
        context.user_data["monto"] = monto
        await update.message.reply_text(
            f"Monto: ${formatear_numero(monto)} COP\n\n"
            "📝 ¿Cuál es la DESCRIPCIÓN del gasto?\n"
            "(Ejemplo: almuerzo, cine, mercado, etc.)"
        )
        return GASTO_DESCRIPCION
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, envía un número válido.\n"
            "Ejemplo: 15000"
        )
        return GASTO_MONTO


async def gasto_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la descripción del gasto."""
    descripcion = update.message.text.strip()
    context.user_data["descripcion"] = descripcion

    mensaje_categorias = "📂 ¿Cuál es la CATEGORÍA?\n\n"
    for num, cat in CATEGORIAS.items():
        mensaje_categorias += f"{num} - {cat['emoji']} {cat['nombre']}\n"
    mensaje_categorias += "\nResponde con el NÚMERO de la categoría:"

    await update.message.reply_text(mensaje_categorias)
    return GASTO_CATEGORIA


async def gasto_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la categoría del gasto."""
    texto = update.message.text.strip()

    try:
        num_categoria = int(texto)
        if num_categoria in CATEGORIAS:
            categoria = CATEGORIAS[num_categoria]["nombre"]
            context.user_data["categoria"] = categoria

            monto = context.user_data["monto"]
            descripcion = context.user_data["descripcion"]
            emoji = CATEGORIAS[num_categoria]["emoji"]

            await update.message.reply_text(
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 REVISA EL GASTO:\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Monto: ${formatear_numero(monto)} COP\n"
                f"📝 Descripción: {descripcion}\n"
                f"📂 Categoría: {emoji} {categoria}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"¿Confirmas este gasto?\n"
                f"Responde: SI o NO"
            )
            return GASTO_CONFIRMAR

        await update.message.reply_text(
            "❌ Número inválido. Elige un número del 1 al 6.\n\n"
            "1 - Comida\n2 - Vivienda\n3 - Compras\n4 - Salud\n5 - Suscripciones\n6 - Otros"
        )
        return GASTO_CATEGORIA
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor, responde con el NÚMERO de la categoría (1 al 6)."
        )
        return GASTO_CATEGORIA


async def gasto_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma o cancela el gasto (incluye alerta de gasto enorme)."""
    chat_id = update.effective_user.id
    respuesta = update.message.text.strip().upper()

    # 1. Confirmación de un gasto grande (segunda vez que el usuario dice SI)
    if context.user_data.get("esperando_confirmacion_grande"):
        if respuesta == "SI":
            monto = context.user_data["monto"]
            descripcion = context.user_data["descripcion"]
            categoria = context.user_data["categoria"]

            await guardar_gasto(chat_id, monto, descripcion, categoria)

            usuario = await obtener_usuario(chat_id)
            ingreso_fijo = usuario["ingreso_fijo"]
            total_gastado = await total_gastado_mes(chat_id)
            total_extra = await total_ingresos_extra_mes(chat_id)
            total_disponible = ingreso_fijo + total_extra
            emoji = get_emoji_categoria(categoria)

            await update.message.reply_text(
                f"✅ GASTO REGISTRADO (confirmado)\n\n"
                f"💰 ${formatear_numero(monto)} COP - {descripcion}\n"
                f"📂 {emoji} {categoria}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Te queda: ${formatear_numero(total_disponible - total_gastado)} COP"
                f"{comandos_con_gasto()}"
            )
            context.user_data.clear()
            return ConversationHandler.END

        elif respuesta == "NO":
            await update.message.reply_text(
                f"❌ Gasto cancelado por precaución."
                f"{comandos_rapidos()}"
            )
            context.user_data.clear()
            return ConversationHandler.END

    # 2. Flujo normal (primera vez que responde)
    if respuesta == "SI":
        monto = context.user_data["monto"]
        descripcion = context.user_data["descripcion"]
        categoria = context.user_data["categoria"]

        usuario = await obtener_usuario(chat_id)
        ingreso_fijo = usuario["ingreso_fijo"]

        if monto > (ingreso_fijo * 0.5):
            await update.message.reply_text(
                f"⚠️ ¡ATENCIÓN! Este gasto de ${formatear_numero(monto)} COP\n"
                f"es mayor al 50% de tu ingreso mensual (${formatear_numero(ingreso_fijo)} COP).\n\n"
                f"¿Estás seguro de que quieres registrarlo?\n"
                f"Responde: SI o NO"
            )
            context.user_data["esperando_confirmacion_grande"] = True
            return GASTO_CONFIRMAR

        await guardar_gasto(chat_id, monto, descripcion, categoria)

        total_gastado = await total_gastado_mes(chat_id)
        total_extra = await total_ingresos_extra_mes(chat_id)
        total_disponible = ingreso_fijo + total_extra
        porcentaje = (total_gastado / total_disponible) * 100 if total_disponible > 0 else 0
        emoji = get_emoji_categoria(categoria)

        mensaje = (
            f"✅ GASTO REGISTRADO\n\n"
            f"💰 ${formatear_numero(monto)} COP - {descripcion}\n"
            f"📂 {emoji} {categoria}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 NUEVO SALDO DEL MES:\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Ingreso fijo: ${formatear_numero(ingreso_fijo)} COP\n"
            f"➕ Ingresos extra: ${formatear_numero(total_extra)} COP\n"
            f"💸 Total gastado: ${formatear_numero(total_gastado)} COP\n"
            f"📊 {porcentaje:.1f}% del total disponible\n"
            f"💰 Te queda: ${formatear_numero(total_disponible - total_gastado)} COP"
        )

        if porcentaje >= 80:
            mensaje += f"\n\n⚠️ ¡ALERTA! Has alcanzado el {porcentaje:.1f}% de tu ingreso mensual. ¡Revisa tus gastos!"

        mensaje += comandos_con_gasto()
        await update.message.reply_text(mensaje)
        context.user_data.clear()
        return ConversationHandler.END

    elif respuesta == "NO":
        await update.message.reply_text(
            f"❌ Gasto cancelado."
            f"{comandos_rapidos()}"
        )
        context.user_data.clear()
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            f"Por favor, responde con SI o NO"
            f"{comandos_rapidos()}"
        )
        return GASTO_CONFIRMAR


# Se reutiliza el entry point "start" como fallback para que, si el usuario
# se atasca en la conversación de un gasto, /start lo lleve al registro/inicio.
from .registro import inicio_registro  # noqa: E402

gasto_handler = ConversationHandler(
    entry_points=[CommandHandler("gasto", inicio_gasto)],
    states={
        GASTO_MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_monto)],
        GASTO_DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_descripcion)],
        GASTO_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_categoria)],
        GASTO_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_confirmar)],
    },
    fallbacks=[CommandHandler("start", inicio_registro)],
)
