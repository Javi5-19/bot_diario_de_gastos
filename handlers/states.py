"""
Estados numéricos usados por los ConversationHandler del bot.
"""

# Estados para registro de usuario (primera vez)
ESPERANDO_CONTRASENA, ESPERANDO_NOMBRE, ESPERANDO_INGRESO, CONFIRMANDO_INGRESO = range(4)

# Estados para registro de gasto
GASTO_MONTO, GASTO_DESCRIPCION, GASTO_CATEGORIA, GASTO_CONFIRMAR = range(4, 8)

# Estados para registro de ingreso extra
EXTRA_MONTO, EXTRA_RAZON, EXTRA_CONFIRMAR = range(8, 11)

# Estado para selección de mes (/mes)
SELECCIONANDO_MES = 11

# Estados para cambiar nombre
NOMBRE_NUEVO, CONFIRMAR_NOMBRE = range(12, 14)

# Estados para borrar todo
BORRAR_CONFIRMAR1, BORRAR_CONTRASENA, BORRAR_CONFIRMAR2 = range(14, 17)
