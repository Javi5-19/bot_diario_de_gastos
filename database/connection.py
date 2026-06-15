"""
Conexión a la base de datos y creación de tablas.
"""

import os
import aiosqlite

# Carpeta donde se guarda la base de datos
DATOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
os.makedirs(DATOS_DIR, exist_ok=True)

DB_PATH = os.path.join(DATOS_DIR, "gastos.db")


async def crear_tablas():
    """Crea las tablas si no existen (se ejecuta una sola vez al iniciar)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Tabla 1: USUARIOS
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                chat_id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                ingreso_fijo INTEGER NOT NULL,
                fecha_registro TEXT NOT NULL
            )
        ''')

        # Tabla 2: GASTOS
        await db.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                monto INTEGER NOT NULL,
                descripcion TEXT,
                categoria TEXT NOT NULL
            )
        ''')

        # Tabla 3: INGRESOS EXTRA
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ingresos_extra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                monto INTEGER NOT NULL,
                razon TEXT
            )
        ''')

        # Tabla 4: CONTADOR DE PROMPTS (límite diario)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS contador_prompts (
                chat_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                cantidad INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, fecha)
            )
        ''')

        await db.commit()

    print("✅ Base de datos inicializada correctamente")
