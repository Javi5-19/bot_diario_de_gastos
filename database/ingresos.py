"""
Operaciones de base de datos relacionadas con los ingresos extra.
"""

from datetime import datetime
import aiosqlite

from .connection import DB_PATH


async def guardar_ingreso_extra(chat_id: int, monto: int, razon: str):
    """Guarda un nuevo ingreso extra."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ingresos_extra (chat_id, fecha, monto, razon)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, fecha, monto, razon))
        await db.commit()


async def total_ingresos_extra_mes(chat_id: int, año_mes: str = None) -> int:
    """Calcula el total de ingresos extra en un mes."""
    if año_mes is None:
        año_mes = datetime.now().strftime("%Y-%m")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT COALESCE(SUM(monto), 0) FROM ingresos_extra
            WHERE chat_id = ? AND strftime('%Y-%m', fecha) = ?
        ''', (chat_id, año_mes)) as cursor:
            resultado = await cursor.fetchone()
            return resultado[0] if resultado else 0


async def obtener_ingresos_extra_mes(chat_id: int, año_mes: str = None):
    """Obtiene la lista de ingresos extra de un mes."""
    if año_mes is None:
        año_mes = datetime.now().strftime("%Y-%m")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT fecha, monto, razon
            FROM ingresos_extra
            WHERE chat_id = ? AND strftime('%Y-%m', fecha) = ?
            ORDER BY fecha DESC
        ''', (chat_id, año_mes)) as cursor:
            resultados = await cursor.fetchall()

    return [
        {"fecha": r[0], "monto": r[1], "razon": r[2]}
        for r in resultados
    ]
