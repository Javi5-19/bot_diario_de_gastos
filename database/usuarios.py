"""
Operaciones de base de datos relacionadas con los usuarios (perfil).
"""

from datetime import datetime
import aiosqlite

from .connection import DB_PATH


async def usuario_existe(chat_id: int) -> bool:
    """Verifica si un usuario ya está registrado."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM usuarios WHERE chat_id = ?", (chat_id,)
        ) as cursor:
            resultado = await cursor.fetchone()
            return resultado is not None


async def registrar_usuario(chat_id: int, nombre: str, ingreso_fijo: int):
    """Registra un nuevo usuario en la base de datos."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO usuarios (chat_id, nombre, ingreso_fijo, fecha_registro)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, nombre, ingreso_fijo, fecha))
        await db.commit()


async def obtener_usuario(chat_id: int):
    """Obtiene los datos de un usuario por su chat_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT chat_id, nombre, ingreso_fijo, fecha_registro FROM usuarios WHERE chat_id = ?",
            (chat_id,)
        ) as cursor:
            resultado = await cursor.fetchone()
            if resultado:
                return {
                    "chat_id": resultado[0],
                    "nombre": resultado[1],
                    "ingreso_fijo": resultado[2],
                    "fecha_registro": resultado[3]
                }
            return None


async def actualizar_ingreso_fijo(chat_id: int, nuevo_ingreso: int):
    """Actualiza el ingreso fijo de un usuario."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE usuarios SET ingreso_fijo = ? WHERE chat_id = ?",
            (nuevo_ingreso, chat_id)
        )
        await db.commit()


async def actualizar_nombre_usuario(chat_id: int, nuevo_nombre: str):
    """Actualiza el nombre de un usuario."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE usuarios SET nombre = ? WHERE chat_id = ?",
            (nuevo_nombre, chat_id)
        )
        await db.commit()


async def borrar_todos_datos_usuario(chat_id: int):
    """Borra TODOS los datos de un usuario (gastos, ingresos extra, contador y perfil)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM gastos WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM ingresos_extra WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM contador_prompts WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM usuarios WHERE chat_id = ?", (chat_id,))
        await db.commit()
