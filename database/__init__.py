"""
Paquete database: capa de acceso a datos (SQLite) del bot.

Este __init__ re-exporta todas las funciones para que el resto del
proyecto pueda seguir haciendo:

    from database import guardar_gasto, obtener_usuario, ...

sin importar de qué submódulo viene cada función.
"""

from .connection import DB_PATH, crear_tablas

from .usuarios import (
    usuario_existe,
    registrar_usuario,
    obtener_usuario,
    actualizar_ingreso_fijo,
    actualizar_nombre_usuario,
    borrar_todos_datos_usuario,
)

from .gastos import (
    guardar_gasto,
    obtener_gastos_mes,
    total_gastado_mes,
    ultimo_gasto,
    eliminar_gasto,
)

from .ingresos import (
    guardar_ingreso_extra,
    total_ingresos_extra_mes,
    obtener_ingresos_extra_mes,
)

from .limites import (
    verificar_limite_prompts,
    meses_con_registros,
)

__all__ = [
    "DB_PATH",
    "crear_tablas",
    "usuario_existe",
    "registrar_usuario",
    "obtener_usuario",
    "actualizar_ingreso_fijo",
    "actualizar_nombre_usuario",
    "borrar_todos_datos_usuario",
    "guardar_gasto",
    "obtener_gastos_mes",
    "total_gastado_mes",
    "ultimo_gasto",
    "eliminar_gasto",
    "guardar_ingreso_extra",
    "total_ingresos_extra_mes",
    "obtener_ingresos_extra_mes",
    "verificar_limite_prompts",
    "meses_con_registros",
]
