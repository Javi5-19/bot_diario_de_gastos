#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)

from config import TOKEN, CONTRASENA, CATEGORIAS, LIMITE_TOKENS, LIMITE_PROMPTS_DIA
from database import (
    usuario_existe, registrar_usuario, obtener_usuario,
    guardar_gasto, total_gastado_mes, total_ingresos_extra_mes,
    ultimo_gasto, eliminar_gasto, verificar_limite_prompts,
    guardar_ingreso_extra, obtener_gastos_mes, obtener_ingresos_extra_mes,
    meses_con_registros, actualizar_ingreso_fijo,
    borrar_todos_datos_usuario, crear_tablas,
    actualizar_nombre_usuario  # <--- AGREGADA PARA CAMBIAR NOMBRE
)

# ==================================================
# PARTE 1: ESTADOS PARA CONVERSACIONES
# ==================================================

# Estados para registro de usuario (primera vez)
ESPERANDO_CONTRASENA, ESPERANDO_NOMBRE, ESPERANDO_INGRESO, CONFIRMANDO_INGRESO = range(4)

# Estados para registro de gasto
GASTO_MONTO, GASTO_DESCRIPCION, GASTO_CATEGORIA, GASTO_CONFIRMAR = range(4, 8)

# Estados para registro de ingreso extra
EXTRA_MONTO, EXTRA_RAZON, EXTRA_CONFIRMAR = range(8, 11)

# Estado para selección de mes (para /mes)
SELECCIONANDO_MES = 11

# Estados para cambiar nombre
NOMBRE_NUEVO, CONFIRMAR_NOMBRE = range(12, 14)

# Estados para borrar todo
BORRAR_CONFIRMAR1, BORRAR_CONTRASENA, BORRAR_CONFIRMAR2 = range(14, 17)

# ==================================================
# PARTE 2: FUNCIONES AUXILIARES
# ==================================================

def formatear_numero(numero: int) -> str:
    """Convierte un número a formato con puntos: 2500000 -> 2.500.000"""
    return f"{numero:,}".replace(",", ".")

def contar_tokens(texto: str) -> int:
    """Cuenta aproximadamente los tokens de un mensaje"""
    palabras = len(re.findall(r'\S+', texto))
    return int(palabras * 1.3)

def validar_tokens(texto: str) -> tuple:
    """Verifica si el mensaje excede el límite de tokens"""
    tokens = contar_tokens(texto)
    if tokens > LIMITE_TOKENS:
        return False, tokens
    return True, tokens

def get_emoji_categoria(categoria: str) -> str:
    """Obtiene el emoji de una categoría por su nombre"""
    for num, cat in CATEGORIAS.items():
        if cat["nombre"] == categoria:
            return cat["emoji"]
    return "💰"

def comandos_rapidos():
    """Retorna el bloque de comandos rápidos básicos (/inicio y /ayuda)"""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/inicio - Ver resumen del mes\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

def comandos_con_gasto():
    """Retorna el bloque de comandos incluyendo /gasto para registrar otro"""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/gasto - Registrar otro gasto\n"
        f"/inicio - Ver resumen del mes\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

def comandos_con_extra():
    """Retorna el bloque de comandos incluyendo /extra para registrar otro"""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/extra - Registrar otro ingreso extra\n"
        f"/inicio - Ver resumen del mes\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

def comandos_inicio():
    """Retorna el bloque de comandos rápidos para /inicio (solo /gasto y /ayuda)"""
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 COMANDOS RÁPIDOS:\n"
        f"/gasto - Registrar un gasto\n"
        f"/ayuda - Ver todos los comandos\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

# ==================================================
# PARTE 3: CONVERSATION HANDLER - REGISTRO (con contraseña)
# ==================================================

async def inicio_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de registro (primera vez)"""
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
    """Verifica la contraseña escrita por el usuario"""
    texto = update.message.text.strip()
    
    if texto == CONTRASENA:
        await update.message.reply_text(
            "✅ CONTRASEÑA CORRECTA\n\n"
            "Ahora necesito registrar tus datos.\n\n"
            "📝 ¿Cómo deseas que me dirija a ti?\n"
            "(Ejemplo: Fernan, Javier, etc.)"
        )
        return ESPERANDO_NOMBRE
    else:
        await update.message.reply_text(
            "❌ CONTRASEÑA INCORRECTA\n\n"
            "La contraseña no es válida. El bot se detendrá para ti.\n"
            "Si crees que es un error, contacta al administrador."
        )
        return ConversationHandler.END

async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el nombre del usuario"""
    nombre = update.message.text.strip()
    context.user_data["nombre"] = nombre
    
    await update.message.reply_text(
        f"Gracias {nombre}.\n\n"
        "💰 ¿Cuál es tu INGRESO MENSUAL FIJO en pesos colombianos?\n"
        "(Ejemplo: 2500000 para dos millones quinientos mil pesos)"
    )
    return ESPERANDO_INGRESO

async def recibir_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el ingreso mensual y pide confirmación"""
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
    """Confirma o rechaza el ingreso mensual"""
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

# ==================================================
# PARTE 4: CONVERSATION HANDLER - GASTO
# ==================================================

async def inicio_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de registro de gasto"""
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
    """Recibe el monto del gasto"""
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
    """Recibe la descripción del gasto"""
    descripcion = update.message.text.strip()
    context.user_data["descripcion"] = descripcion
    
    mensaje_categorias = "📂 ¿Cuál es la CATEGORÍA?\n\n"
    for num, cat in CATEGORIAS.items():
        mensaje_categorias += f"{num} - {cat['emoji']} {cat['nombre']}\n"
    mensaje_categorias += "\nResponde con el NÚMERO de la categoría:"
    
    await update.message.reply_text(mensaje_categorias)
    return GASTO_CATEGORIA

async def gasto_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la categoría del gasto"""
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
        else:
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
    """Confirma o cancela el gasto (incluye alerta de gasto enorme)"""
    chat_id = update.effective_user.id
    respuesta = update.message.text.strip().upper()
    
    # 1. Verificar si es la confirmación de un gasto grande (segunda vez que el usuario dice SI)
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

# ==================================================
# PARTE 5: CONVERSATION HANDLER - INGRESO EXTRA
# ==================================================

async def inicio_extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de registro de ingreso extra"""
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
    """Recibe el monto del ingreso extra"""
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
    """Recibe la razón del ingreso extra"""
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
    """Confirma o cancela el ingreso extra"""
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

# ==================================================
# PARTE 6: CONVERSATION HANDLER - CAMBIAR NOMBRE
# ==================================================

async def cambiar_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso para cambiar el nombre del usuario"""
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
    """Recibe el nuevo nombre y pide confirmación"""
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
    """Confirma o cancela el cambio de nombre"""
    chat_id = update.effective_user.id
    respuesta = update.message.text.strip().upper()
    
    if respuesta == "SI":
        nuevo_nombre = context.user_data["nuevo_nombre"]
        usuario = await obtener_usuario(chat_id)
        nombre_anterior = usuario["nombre"]
        
        # Usar la función importada desde database.py
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

# ==================================================
# PARTE 7: CONVERSATION HANDLER - BORRAR TODO
# ==================================================

async def borrar_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso para borrar todos los datos del usuario"""
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
    """Primera confirmación de borrado"""
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
            f"Por favor, responde con SI o NO"
        )
        return BORRAR_CONFIRMAR1

async def borrar_contrasena(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica la contraseña"""
    contrasena_ingresada = update.message.text.strip()
    
    if contrasena_ingresada == CONTRASENA:
        await update.message.reply_text(
            "🔄 ÚLTIMA CONFIRMACIÓN\n\n"
            "Para borrar TODOS tus datos, escribe:\n"
            "BORRAR MIS DATOS"
        )
        return BORRAR_CONFIRMAR2
    else:
        await update.message.reply_text(
            f"❌ Contraseña incorrecta. Operación cancelada."
            f"{comandos_rapidos()}"
        )
        return ConversationHandler.END

async def borrar_confirmar2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Segunda confirmación de borrado con texto específico"""
    respuesta = update.message.text.strip()
    chat_id = update.effective_user.id
    
    if respuesta == "BORRAR MIS DATOS":
        # Borrar todos los datos del usuario
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
    else:
        await update.message.reply_text(
            f"❌ Confirmación incorrecta. Operación cancelada.\n\n"
            f"Tus datos están seguros."
            f"{comandos_rapidos()}"
        )
        return ConversationHandler.END

# ==================================================
# PARTE 8: COMANDOS SIMPLES
# ==================================================

async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el resumen del mes actual con comandos rápidos"""
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

async def lista_gastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de gastos del mes actual"""
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
        fecha = g["fecha"]
        if fecha not in gastos_por_fecha:
            gastos_por_fecha[fecha] = []
        gastos_por_fecha[fecha].append(g)
    
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

async def ver_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de meses disponibles para elegir por número"""
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
        except:
            mensaje += f"{i}. {mes}\n"
    
    mensaje += "\n📝 Responde con el NÚMERO del mes que quieres ver:"
    await update.message.reply_text(mensaje)
    return SELECCIONANDO_MES

async def seleccionar_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la selección numérica del mes"""
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
            except:
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
        else:
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

async def cambiar_ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cambia el ingreso fijo mensual"""
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

async def deshacer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina el último gasto registrado"""
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

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de comandos disponibles"""
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

# ==================================================
# PARTE 9: FUNCIÓN POST_INIT (inicialización segura de DB)
# ==================================================

async def post_init(application: Application):
    """Se ejecuta después de inicializar la aplicación y antes de empezar a recibir mensajes"""
    print("🔧 Inicializando base de datos...")
    await crear_tablas()
    print("✅ Base de datos lista.")

# ==================================================
# PARTE 10: FUNCIÓN PRINCIPAL
# ==================================================

def main():
    """Función principal que inicia el bot"""
    
    print("🚀 Iniciando Libreta de Gastos Bot...")
    print(f"📊 Límite de prompts por día: {LIMITE_PROMPTS_DIA}")
    print(f"🔐 Contraseña configurada: {CONTRASENA}")
    
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # ConversationHandler para registro
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
    
    # ConversationHandler para gasto
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
    
    # ConversationHandler para ingreso extra
    extra_handler = ConversationHandler(
        entry_points=[CommandHandler("extra", inicio_extra)],
        states={
            EXTRA_MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_monto)],
            EXTRA_RAZON: [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_razon)],
            EXTRA_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_confirmar)],
        },
        fallbacks=[CommandHandler("start", inicio_registro)],
    )
    
    # ConversationHandler para /mes (selección numérica)
    mes_handler = ConversationHandler(
        entry_points=[CommandHandler("mes", ver_mes)],
        states={
            SELECCIONANDO_MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_mes)],
        },
        fallbacks=[CommandHandler("mes", ver_mes)],
    )
    
    # ConversationHandler para cambiar nombre
    nombre_handler = ConversationHandler(
        entry_points=[CommandHandler("cambiar_nombre", cambiar_nombre)],
        states={
            NOMBRE_NUEVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nuevo_nombre)],
            CONFIRMAR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_nombre)],
        },
        fallbacks=[CommandHandler("inicio", inicio)],
    )
    
    # ConversationHandler para borrar todo
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
    
    # Registrar handlers
    app.add_handler(registro_handler)
    app.add_handler(gasto_handler)
    app.add_handler(extra_handler)
    app.add_handler(mes_handler)
    app.add_handler(nombre_handler)
    app.add_handler(borrar_handler)
    app.add_handler(CommandHandler("inicio", inicio))
    app.add_handler(CommandHandler("lista", lista_gastos))
    app.add_handler(CommandHandler("ingreso", cambiar_ingreso))
    app.add_handler(CommandHandler("deshacer", deshacer))
    app.add_handler(CommandHandler("ayuda", ayuda))
    
    print("✅ BOT FUNCIONANDO...")
    print("Presiona Ctrl+C para detener el bot")
    
    app.run_polling()

if __name__ == "__main__":
    main()