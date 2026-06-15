import os
import aiosqlite
from datetime import datetime
from config import LIMITE_PROMPTS_DIA

# ==================================================
# PARTE 1: RUTA DE LA BASE DE DATOS
# ==================================================

# Crear la carpeta "datos" si no existe
if not os.path.exists("datos"):
    os.makedirs("datos")

DB_PATH = "datos/gastos.db"

# ==================================================
# PARTE 2: CREAR TABLAS (asíncrono)
# ==================================================

async def crear_tablas():
    """Crea las tablas si no existen (se ejecuta una sola vez al iniciar)"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Tabla 1: USUARIOS
        # chat_id es la clave principal (el ID que Telegram asigna a cada persona)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                chat_id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                ingreso_fijo INTEGER NOT NULL,
                fecha_registro TEXT NOT NULL
            )
        ''')
        
        # Tabla 2: GASTOS
        # Usa chat_id directamente (sin JOIN innecesario)
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
        
        # Tabla 4: CONTADOR DE PROMPTS (para límite diario)
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

# ==================================================
# PARTE 3: FUNCIONES PARA USUARIOS
# ==================================================

async def usuario_existe(chat_id: int) -> bool:
    """Verifica si un usuario ya está registrado"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM usuarios WHERE chat_id = ?", (chat_id,)
        ) as cursor:
            resultado = await cursor.fetchone()
            return resultado is not None

async def registrar_usuario(chat_id: int, nombre: str, ingreso_fijo: int):
    """Registra un nuevo usuario en la base de datos"""
    fecha = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO usuarios (chat_id, nombre, ingreso_fijo, fecha_registro)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, nombre, ingreso_fijo, fecha))
        await db.commit()

async def obtener_usuario(chat_id: int):
    """Obtiene los datos de un usuario por su chat_id"""
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
    """Actualiza el ingreso fijo de un usuario"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE usuarios SET ingreso_fijo = ? WHERE chat_id = ?",
            (nuevo_ingreso, chat_id)
        )
        await db.commit()

# ==================================================
# PARTE 4: FUNCIONES PARA GASTOS
# ==================================================

async def guardar_gasto(chat_id: int, monto: int, descripcion: str, categoria: str):
    """Guarda un nuevo gasto en la base de datos"""
    fecha = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO gastos (chat_id, fecha, monto, descripcion, categoria)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, fecha, monto, descripcion, categoria))
        await db.commit()

async def obtener_gastos_mes(chat_id: int, año_mes: str = None):
    """Obtiene todos los gastos de un mes específico"""
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
    """Calcula el total gastado en un mes"""
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
    """Obtiene el último gasto de un usuario"""
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
    """Elimina un gasto por su ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        await db.commit()

# ==================================================
# PARTE 5: FUNCIONES PARA INGRESOS EXTRA
# ==================================================

async def guardar_ingreso_extra(chat_id: int, monto: int, razon: str):
    """Guarda un nuevo ingreso extra"""
    fecha = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ingresos_extra (chat_id, fecha, monto, razon)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, fecha, monto, razon))
        await db.commit()

async def total_ingresos_extra_mes(chat_id: int, año_mes: str = None) -> int:
    """Calcula el total de ingresos extra en un mes"""
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
    """Obtiene la lista de ingresos extra de un mes"""
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

# ==================================================
# PARTE 6: FUNCIONES PARA LÍMITE DE PROMPTS
# ==================================================

async def verificar_limite_prompts(chat_id: int):
    """Verifica si el usuario ha superado el límite de prompts por día"""
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT cantidad FROM contador_prompts 
            WHERE chat_id = ? AND fecha = ?
        ''', (chat_id, hoy)) as cursor:
            resultado = await cursor.fetchone()
        
        if resultado:
            cantidad = resultado[0]
            # CORRECCIÓN: Usar la constante desde config.py
            if cantidad >= LIMITE_PROMPTS_DIA:
                return False, 0
            else:
                nueva_cantidad = cantidad + 1
                await db.execute('''
                    UPDATE contador_prompts SET cantidad = ? 
                    WHERE chat_id = ? AND fecha = ?
                ''', (nueva_cantidad, chat_id, hoy))
                await db.commit()
                return True, LIMITE_PROMPTS_DIA - nueva_cantidad
        else:
            await db.execute('''
                INSERT INTO contador_prompts (chat_id, fecha, cantidad)
                VALUES (?, ?, 1)
            ''', (chat_id, hoy))
            await db.commit()
            return True, LIMITE_PROMPTS_DIA - 1

# ==================================================
# PARTE 7: FUNCIONES PARA MESES DISPONIBLES
# ==================================================

async def meses_con_registros(chat_id: int):
    """Devuelve una lista de meses que tienen gastos o ingresos extra"""
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


# ==================================================
# PARTE 8: FUNCIONES PARA ACTUALIZAR NOMBRE Y BORRAR DATOS
# ==================================================

async def actualizar_nombre_usuario(chat_id: int, nuevo_nombre: str):
    """Actualiza el nombre de un usuario"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE usuarios SET nombre = ? WHERE chat_id = ?",
            (nuevo_nombre, chat_id)
        )
        await db.commit()

async def borrar_todos_datos_usuario(chat_id: int):
    """Borra TODOS los datos de un usuario (gastos, ingresos extra, contador, y perfil)"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Borrar gastos
        await db.execute("DELETE FROM gastos WHERE chat_id = ?", (chat_id,))
        # Borrar ingresos extra
        await db.execute("DELETE FROM ingresos_extra WHERE chat_id = ?", (chat_id,))
        # Borrar contador de prompts
        await db.execute("DELETE FROM contador_prompts WHERE chat_id = ?", (chat_id,))
        # Borrar usuario (perfil)
        await db.execute("DELETE FROM usuarios WHERE chat_id = ?", (chat_id,))
        await db.commit()

# ==================================================
# NOTA: NO HAY INICIALIZACIÓN AUTOMÁTICA
# La función crear_tablas() se ejecuta desde bot.py en post_init
# ==================================================