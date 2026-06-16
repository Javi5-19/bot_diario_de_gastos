# Bot Diario de Gastos

Este proyecto es un bot de Telegram para llevar una libreta personal de gastos.

El bot ayuda a registrar gastos, ingresos extra y consultar cuánto dinero queda disponible durante el mes.

## Integrantes

- Wilson Javier Alzate Contreras
- Moises David Bolivar
- Leonel Vanegas Pinedo
- Yais Martinez Rosado

## Problema que resuelve el bot

La mayoría de las personas no llevan un control de sus gastos diarios porque las aplicaciones existentes suelen ser algo "complejas" o requieren descargar apps adicionales. Este bot aprovecha Telegram (app de mensajería conocida por la privacidad que le otorga a los usuarios y por ende muy popular a nivel mundial) para ofrecer una solución simple, rápida y accesible desde cualquier dispositivo.

## Uso de inteligencia artificial

Este proyecto fue codificado con asistencia de IA.

Las herramientas utilizadas fueron:

- ChatGPT, Claude, Deepseek y Z.ai: generación de código, optimización del código.
- Gemini: utilizada para resolver dudas menores del funcionamiento del proyecto.

## Qué hace el bot

- Registra usuarios con una contraseña privada.
- Guarda el ingreso mensual fijo de cada usuario.
- Permite registrar gastos con monto, descripción y categoría.
- Permite registrar ingresos extra.
- Muestra un resumen del mes actual.
- Muestra la lista de gastos del mes.
- Permite consultar meses anteriores.
- Permite cambiar el nombre del usuario.
- Permite cambiar el ingreso mensual fijo.
- Permite eliminar el último gasto registrado.
- Permite borrar todos los datos de un usuario con confirmación.
- Guarda la información en una base de datos SQLite.

## Tecnologías usadas

- Python
- Telegram Bot API
- SQLite
- python-telegram-bot
- python-dotenv
- aiosqlite

## Estructura del proyecto
bot_diario_de_gastos/
│
├── main.py # Punto de entrada principal
├── config.py # Configuración y constantes
├── requirements.txt # Dependencias del proyecto
├── Procfile # Comando de inicio para Railway
├── README.md # Documentación
│
├── database/ # Capa de acceso a datos
│ ├── init.py # Re-exporta todas las funciones
│ ├── connection.py # Conexión a SQLite y creación de tablas
│ ├── usuarios.py # CRUD de usuarios
│ ├── gastos.py # CRUD de gastos
│ ├── ingresos.py # CRUD de ingresos extra
│ └── limites.py # Límite de prompts y meses disponibles
│
├── handlers/ # Lógica de comandos
│ ├── init.py # Registro de handlers
│ ├── states.py # Estados de conversación
│ ├── helpers.py # Funciones auxiliares (formateo, comandos)
│ ├── registro.py # /start y registro
│ ├── gasto.py # /gasto
│ ├── extra.py # /extra
│ ├── consultas.py # /inicio, /lista, /mes, /deshacer, /ayuda
│ ├── perfil.py # /ingreso, /cambiar_nombre
│ └── borrar.py # /borrar_todo, /reset
│
└── datos/ # Carpeta de la base de datos 
└── gastos.db # Base de datos SQLite

## Instalación

1. Instala Python.

2. Instala las dependencias del proyecto:

pip install -r requirements.txt

3. Crea un archivo llamado .env en la raíz del proyecto.

4. Agrega la configuración:

TOKEN=tu_token_de_telegram
CONTRASENA=proyecto2026
HORA_RECORDATORIO=20:00

El TOKEN es obligatorio. Se obtiene creando un bot con BotFather en Telegram.
La CONTRASENA es la clave que una persona debe escribir para poder registrarse en el bot.

## Cómo ejecutar el bot

Ejecuta:

python main.py

Si la configuración es correcta, el bot queda encendido y esperando mensajes en Telegram.

Para detenerlo, presiona Ctrl + C en la terminal.

## Primer uso en Telegram

1. Abre el chat con el bot.
2. Escribe /start.
3. Ingresa la contraseña.
4. Escribe tu nombre.
5. Escribe tu ingreso mensual fijo.
6. Confirma la información con SI.

Después del registro ya puedes usar los demás comandos.

## Comandos disponibles

Registros:
- /gasto: registra un gasto paso a paso.
- /extra: registra un ingreso extra paso a paso.

Consultas:
- /inicio: muestra el resumen del mes actual.
- /lista: muestra la lista de gastos del mes actual.
- /mes: permite elegir un mes con registros y ver su resumen.

Perfil y edición:
- /ingreso [monto]: cambia el ingreso mensual fijo.
- /cambiar_nombre: cambia el nombre del usuario.
- /deshacer: elimina el último gasto registrado.

Borrado:
- /borrar_todo: elimina todos los datos del usuario después de varias confirmaciones.
- /reset: hace lo mismo que /borrar_todo.

Ayuda:
- /ayuda: muestra la lista de comandos dentro de Telegram.

## Categorías de gastos

Cuando registras un gasto, el bot pide elegir una categoría:

1. Comida
2. Vivienda
3. Compras
4. Salud
5. Suscripciones
6. Otros

## Base de datos

El proyecto crea automáticamente una carpeta llamada datos.

Dentro de esa carpeta se guarda la base de datos:

datos/gastos.db

## Límites y alertas

- Cada usuario tiene un límite de 100 mensajes por día.
- Cada mensaje tiene un límite aproximado de 4000 tokens.
- Si un gasto supera el 50% del ingreso mensual, el bot pide una confirmación adicional.
- Si el usuario gasta el 80% o más de su dinero disponible, el bot muestra una alerta.

## Despliegue

El bot se ejecuta como un proceso de fondo.

El comando principal del proyecto actual es:

python main.py

El archivo Procfile ya está configurado con:

worker: python main.py

---

Fecha de entrega: 17 de junio de 2026