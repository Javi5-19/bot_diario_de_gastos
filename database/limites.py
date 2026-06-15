"""
Operaciones de base de datos para el límite diario de mensajes
y la consulta de meses con registros.
"""

from datetime import datetime
import aiosqlite

from .connection import DB_PATH
from config import LIMITE_PROMPTS_DIA


async def verificar_limite_prompts(chat_id: int):
    """Verifica si el usuario ha superado el límite de mensajes por día."""
    hoy = datetime.now().strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT cantidad FROM contador_prompts
            WHERE chat_id = ? AND fecha = ?
        ''', (chat_id, hoy)) as cursor:
            resultado = await cursor.fetchone()

        if resultado:
            cantidad = resultado[0]
            if cantidad >= LIMITE_PROMPTS_DIA:
                return False, 0

            nueva_cantidad = cantidad + 1
            await db.execute('''
                UPDATE contador_prompts SET cantidad = ?
                WHERE chat_id = ? AND fecha = ?
            ''', (nueva_cantidad, chat_id, hoy))
            await db.commit()
            return True, LIMITE_PROMPTS_DIA - nueva_cantidad

        await db.execute('''
            INSERT INTO contador_prompts (chat_id, fecha, cantidad)
            VALUES (?, ?, 1)
        ''', (chat_id, hoy))
        await db.commit()
        return True, LIMITE_PROMPTS_DIA - 1


async def meses_con_registros(chat_id: int):
    """Devuelve una lista de meses (AAAA-MM) que tienen gastos o ingresos extra."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT DISTINCT strftime('%Y-%m', fecha) as mes
            FROM gastos WHERE chat_id = ?
            UNION
            SELECT DISTINCT strftime('%Y-%m', fecha) as mes
            FROM ingresos_extra WHERE chat_id = ?
            ORDER BY mes DESC
        ''', (chat_id, chat_id)) as cursor:
            resultados = await cursor.fetchall()

    return [r[0] for r in resultados]
