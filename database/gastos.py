"""
Operaciones de base de datos relacionadas con los gastos.
"""

from datetime import datetime
import aiosqlite

from .connection import DB_PATH


async def guardar_gasto(chat_id: int, monto: int, descripcion: str, categoria: str):
    """Guarda un nuevo gasto en la base de datos."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO gastos (chat_id, fecha, monto, descripcion, categoria)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, fecha, monto, descripcion, categoria))
        await db.commit()


async def obtener_gastos_mes(chat_id: int, año_mes: str = None):
    """Obtiene todos los gastos de un mes específico."""
    if año_mes is None:
        año_mes = datetime.now().strftime("%Y-%m")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT fecha, monto, descripcion, categoria
            FROM gastos
            WHERE chat_id = ? AND strftime('%Y-%m', fecha) = ?
            ORDER BY fecha DESC
        ''', (chat_id, año_mes)) as cursor:
            resultados = await cursor.fetchall()

    return [
        {"fecha": r[0], "monto": r[1], "descripcion": r[2], "categoria": r[3]}
        for r in resultados
    ]


async def total_gastado_mes(chat_id: int, año_mes: str = None) -> int:
    """Calcula el total gastado en un mes."""
    if año_mes is None:
        año_mes = datetime.now().strftime("%Y-%m")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT COALESCE(SUM(monto), 0) FROM gastos
            WHERE chat_id = ? AND strftime('%Y-%m', fecha) = ?
        ''', (chat_id, año_mes)) as cursor:
            resultado = await cursor.fetchone()
            return resultado[0] if resultado else 0


async def ultimo_gasto(chat_id: int):
    """Obtiene el último gasto de un usuario."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT id, fecha, monto, descripcion, categoria
            FROM gastos
            WHERE chat_id = ?
            ORDER BY id DESC LIMIT 1
        ''', (chat_id,)) as cursor:
            resultado = await cursor.fetchone()
            if resultado:
                return {
                    "id": resultado[0],
                    "fecha": resultado[1],
                    "monto": resultado[2],
                    "descripcion": resultado[3],
                    "categoria": resultado[4]
                }
            return None


async def eliminar_gasto(gasto_id: int):
    """Elimina un gasto por su ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        await db.commit()
