"""
Comandos de consulta y otros comandos simples:
/inicio, /lista, /mes (conversación), /deshacer, /ayuda.
"""

from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import LIMITE_PROMPTS_DIA
from database import (
    usuario_existe, obtener_usuario, verificar_limite_prompts,
    obtener_gastos_mes, total_gastado_mes, total_ingresos_extra_mes,
    meses_con_registros, ultimo_gasto, eliminar_gasto,
)
from .helpers import formatear_numero, get_emoji_categoria, comandos_rapidos, comandos_inicio
from .states import SELECCIONANDO_MES


# ----------------------------------------------------------------------
# /inicio - resumen del mes actual
# ----------------------------------------------------------------------

async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el resumen del mes actual con comandos rápidos."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 Primero debes registrarte. Escribe /start")
        return

    permitido, _ = await verificar_limite_prompts(chat_id)
    if not permitido:
        await update.message.reply_text(
            f"❌ Llegaste al límite de {LIMITE_PROMPTS_DIA} mensajes por día."
            f"{comandos_rapidos()}"
        )
        return

    usuario = await obtener_usuario(chat_id)
    mes_actual = datetime.now().strftime("%B %Y")

    total_gastado = await total_gastado_mes(chat_id)
    total_extra = await total_ingresos_extra_mes(chat_id)
    total_disponible = usuario["ingreso_fijo"] + total_extra
    restante = total_disponible - total_gastado
    porcentaje = (total_gastado / total_disponible) * 100 if total_disponible > 0 else 0

    mensaje = (
        f"🏠 LIBRETA DE GASTOS DE: {usuario['nombre']}\n\n"
        f"📅 MES: {mes_actual}\n\n"
        f"💰 INGRESO FIJO DEL MES: ${formatear_numero(usuario['ingreso_fijo'])} COP\n"
        f"➕ INGRESOS EXTRA (este mes): ${formatear_numero(total_extra)} COP\n"
        f"💸 TOTAL GASTADO: ${formatear_numero(total_gastado)} COP\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 DINERO QUE QUEDA: ${formatear_numero(restante)} COP\n"
        f"📊 PORCENTAJE GASTADO: {porcentaje:.1f}%\n"
    )

    if porcentaje >= 80:
        mensaje += f"\n⚠️ ¡ALERTA! Has alcanzado el {porcentaje:.1f}% de tu ingreso mensual."

    mensaje += comandos_inicio()

    await update.message.reply_text(mensaje)


# ----------------------------------------------------------------------
# /lista - lista de gastos del mes actual
# ----------------------------------------------------------------------

async def lista_gastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de gastos del mes actual."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 Primero debes registrarte. Escribe /start")
        return

    usuario = await obtener_usuario(chat_id)
    gastos = await obtener_gastos_mes(chat_id)

    if not gastos:
        await update.message.reply_text(
            f"📋 LISTA DE GASTOS DE: {usuario['nombre']}\n\n"
            f"No hay gastos registrados este mes."
            f"{comandos_rapidos()}"
        )
        return

    gastos_por_fecha = {}
    for g in gastos:
        gastos_por_fecha.setdefault(g["fecha"], []).append(g)

    mensaje = f"📋 LISTA DE GASTOS DE: {usuario['nombre']}\n\n"
    total_gastos = 0

    for fecha in sorted(gastos_por_fecha.keys(), reverse=True):
        mensaje += f"📅 {fecha}:\n"
        for g in gastos_por_fecha[fecha]:
            emoji = get_emoji_categoria(g["categoria"])
            mensaje += f"   - ${formatear_numero(g['monto'])} - {g['descripcion']} ({emoji} {g['categoria']})\n"
            total_gastos += 1
        mensaje += "\n"

    mensaje += f"━━━━━━━━━━━━━━━━━━━━━\n"
    mensaje += f"Total de gastos: {total_gastos}"

    if len(mensaje) > 4000:
        await update.message.reply_text("📋 La lista es muy larga. Usa /mes para seleccionar un mes específico.")
    else:
        await update.message.reply_text(mensaje + comandos_rapidos())


# ----------------------------------------------------------------------
# /mes - resumen de un mes específico (conversación)
# ----------------------------------------------------------------------

async def ver_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de meses disponibles para elegir por número."""
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

    meses = await meses_con_registros(chat_id)

    if not meses:
        await update.message.reply_text(
            f"📆 No hay registros de meses anteriores.\n\n"
            f"Usa /inicio para ver el mes actual."
            f"{comandos_rapidos()}"
        )
        return ConversationHandler.END

    context.user_data["meses_disponibles"] = meses

    mensaje = "📆 MESES CON REGISTROS:\n\n"
    for i, mes in enumerate(meses, 1):
        try:
            año, mes_num = mes.split("-")
            nombre_mes = datetime(int(año), int(mes_num), 1).strftime("%B")
            mensaje += f"{i}. {nombre_mes} {año}\n"
        except ValueError:
            mensaje += f"{i}. {mes}\n"

    mensaje += "\n📝 Responde con el NÚMERO del mes que quieres ver:"
    await update.message.reply_text(mensaje)
    return SELECCIONANDO_MES


async def seleccionar_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la selección numérica del mes."""
    chat_id = update.effective_user.id
    texto = update.message.text.strip()

    meses = context.user_data.get("meses_disponibles", [])

    if not meses:
        await update.message.reply_text(
            f"❌ No hay meses disponibles."
            f"{comandos_rapidos()}"
        )
        return ConversationHandler.END

    try:
        numero = int(texto)
        if 1 <= numero <= len(meses):
            mes_consulta = meses[numero - 1]
            usuario = await obtener_usuario(chat_id)

            total_gastado = await total_gastado_mes(chat_id, mes_consulta)
            total_extra = await total_ingresos_extra_mes(chat_id, mes_consulta)
            total_disponible = usuario["ingreso_fijo"] + total_extra
            restante = total_disponible - total_gastado
            porcentaje = (total_gastado / total_disponible) * 100 if total_disponible > 0 else 0

            try:
                año, mes_num = mes_consulta.split("-")
                nombre_mes = datetime(int(año), int(mes_num), 1).strftime("%B %Y")
            except ValueError:
                nombre_mes = mes_consulta

            mensaje = (
                f"📆 RESUMEN DE {nombre_mes} - {usuario['nombre']}\n\n"
                f"💰 INGRESO FIJO: ${formatear_numero(usuario['ingreso_fijo'])} COP\n"
                f"➕ INGRESOS EXTRA: ${formatear_numero(total_extra)} COP\n"
                f"💸 TOTAL GASTADO: ${formatear_numero(total_gastado)} COP\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 SOBRANTE/DÉFICIT: ${formatear_numero(restante)} COP\n"
                f"📊 PORCENTAJE USADO: {porcentaje:.1f}%"
            )

            await update.message.reply_text(mensaje + comandos_rapidos())
            context.user_data.clear()
            return ConversationHandler.END

        await update.message.reply_text(
            f"❌ Número inválido. Elige un número del 1 al {len(meses)}."
            f"{comandos_rapidos()}"
        )
        return SELECCIONANDO_MES
    except ValueError:
        await update.message.reply_text(
            f"❌ Por favor, responde con el NÚMERO del mes."
            f"{comandos_rapidos()}"
        )
        return SELECCIONANDO_MES


mes_handler = ConversationHandler(
    entry_points=[CommandHandler("mes", ver_mes)],
    states={
        SELECCIONANDO_MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_mes)],
    },
    fallbacks=[CommandHandler("mes", ver_mes)],
)


# ----------------------------------------------------------------------
# /deshacer - elimina el último gasto registrado
# ----------------------------------------------------------------------

async def deshacer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina el último gasto registrado."""
    chat_id = update.effective_user.id

    if not await usuario_existe(chat_id):
        await update.message.reply_text("🔐 Primero debes registrarte. Escribe /start")
        return

    ultimo = await ultimo_gasto(chat_id)

    if not ultimo:
        await update.message.reply_text(
            f"❌ No hay gastos para deshacer."
            f"{comandos_rapidos()}"
        )
        return

    await eliminar_gasto(ultimo["id"])

    usuario = await obtener_usuario(chat_id)
    total_gastado = await total_gastado_mes(chat_id)
    total_extra = await total_ingresos_extra_mes(chat_id)
    total_disponible = usuario["ingreso_fijo"] + total_extra
    emoji = get_emoji_categoria(ultimo["categoria"])

    await update.message.reply_text(
        f"↩️ ÚLTIMO GASTO ELIMINADO:\n"
        f"   ${formatear_numero(ultimo['monto'])} - {ultimo['descripcion']} ({emoji} {ultimo['categoria']})\n"
        f"   Fecha: {ultimo['fecha']}\n\n"
        f"💰 Nuevo total del mes: ${formatear_numero(total_gastado)} COP\n"
        f"💰 Te queda: ${formatear_numero(total_disponible - total_gastado)} COP"
        f"{comandos_rapidos()}"
    )


# ----------------------------------------------------------------------
# /ayuda - lista de comandos disponibles
# ----------------------------------------------------------------------

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de comandos disponibles."""
    mensaje = (
        "📖 COMANDOS - LIBRETA DE GASTOS\n\n"
        "💰 REGISTROS:\n"
        "/gasto - Registrar un gasto (paso a paso)\n"
        "/extra - Registrar ingreso extra (paso a paso)\n\n"
        "📊 CONSULTAS:\n"
        "/inicio - Resumen del mes actual\n"
        "/lista - Lista de gastos del mes\n"
        "/mes - Ver resumen de un mes específico (elige por número)\n\n"
        "✏️ EDICIÓN:\n"
        "/ingreso [monto] - Cambiar ingreso fijo\n"
        "/cambiar_nombre - Cambiar tu nombre de usuario\n"
        "/deshacer - Eliminar último gasto\n"
        "/borrar_todo - ELIMINAR TODOS TUS DATOS (requiere confirmación)\n"
        "/reset - Mismo que /borrar_todo\n\n"
        "⚙️ OTROS:\n"
        "/ayuda - Mostrar este mensaje\n\n"
        "📌 CATEGORÍAS:\n"
        "1 - Comida 🍽️\n"
        "2 - Vivienda 🏠\n"
        "3 - Compras 🛍️\n"
        "4 - Salud 🏥\n"
        "5 - Suscripciones 📺\n"
        "6 - Otros 💰"
    )
    await update.message.reply_text(mensaje)
