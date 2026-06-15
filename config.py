import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Token del bot (de BotFather) - Obligatorio
TOKEN = os.getenv("TOKEN")

# VALIDACIÓN FAIL-FAST: Si no hay token, el bot NO ARRANCA
if not TOKEN:
    raise ValueError(
        "❌ ERROR CRÍTICO: No se encontró el TOKEN.\n"
        "Asegúrate de que el archivo .env existe y contiene:\n"
        "TOKEN=tu_token_aqui\n"
        "CONTRASENA=proyecto2026"
    )

# Contraseña para usar el bot
CONTRASENA = os.getenv("CONTRASENA", "proyecto2026")

# Hora del recordatorio diario (formato 24h)
HORA_RECORDATORIO = os.getenv("HORA_RECORDATORIO", "20:00")

# Límites
LIMITE_PROMPTS_DIA = 100      # Máximo 100 mensajes por día por usuario
LIMITE_TOKENS = 4000          # Máximo 4000 tokens por mensaje

# Categorías disponibles (6 categorías)
CATEGORIAS = {
    1: {"nombre": "Comida", "emoji": "🍽️"},
    2: {"nombre": "Vivienda", "emoji": "🏠"},
    3: {"nombre": "Compras", "emoji": "🛍️"},
    4: {"nombre": "Salud", "emoji": "🏥"},
    5: {"nombre": "Suscripciones", "emoji": "📺"},
    6: {"nombre": "Otros", "emoji": "💰"}
}

print("✅ Configuración cargada correctamente")