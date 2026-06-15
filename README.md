# Bot Diario de Gastos 


Este proyecto es un bot de Telegram para llevar una libreta personal de gastos.

El bot ayuda a registrar gastos, ingresos extra y consultar cuanto dinero queda disponible durante el mes.

## integrantes

Wilson javier Alzate contreras

Moises David Bolivar

Leonel Vanegas Pinedo

Yais Martinez Rosado 

## problema que resuelve el bot

La mayoria de personas no llevan un control de sus gastos diarios por que las aplicaciones existentes
suelen ser algo "complejas" o requieren descargar apps adicionales... Este bot aprovecha 
telegram (app de mensajeria conocida por la privacidad que le otorga a los usuarios y por ende muy popular a nivel mundial) para ofrecer una solucion simple rapida y accesible desde cualquier dispositivo. 

## Que hace el bot

- Registra usuarios con una contrasena privada.
- Guarda el ingreso mensual fijo de cada usuario.
- Permite registrar gastos con monto, descripcion y categoria.
- Permite registrar ingresos extra.
- Muestra un resumen del mes actual.
- Muestra la lista de gastos del mes.
- Permite consultar meses anteriores.
- Permite cambiar el nombre del usuario.
- Permite cambiar el ingreso mensual fijo.
- Permite eliminar el ultimo gasto registrado.
- Permite borrar todos los datos de un usuario con confirmacion.
- Guarda la informacion en una base de datos SQLite.

## Tecnologias usadas

- Python
- Telegram Bot API
- SQLite
- `python-telegram-bot`
- `python-dotenv`
- `aiosqlite`

## Estructura del proyecto


bot_diario_de_gastos/
  main.py
  config.py
  requirements.txt
  Procfile
  README.md
  handlers/
    __init__.py
    states.py
    helpers.py
    registro.py
    gasto.py
    extra.py
    consultas.py
    perfil.py
    borrar.py
  database/
    __init__.py
    connection.py
    usuarios.py
    gastos.py
    ingresos.py
    limites.py
## que funcionalidad tiene cada parte del proyecto

- `main.py`: es el punto de entrada del proyecto. Crea la aplicacion de Telegram, registra los handlers y arranca el bot.
- `config.py`: carga la configuracion desde el archivo `.env`.
- `handlers/`: contiene la logica de los comandos y conversaciones del bot.
- `handlers/registro.py`: maneja el registro inicial con `/start`.
- `handlers/gasto.py`: maneja el registro de gastos con `/gasto`.
- `handlers/extra.py`: maneja ingresos extra con `/extra`.
- `handlers/consultas.py`: maneja consultas como `/inicio`, `/lista`, `/mes`, `/deshacer` y `/ayuda`.
- `handlers/perfil.py`: maneja cambios de nombre e ingreso mensual.
- `handlers/borrar.py`: maneja el borrado total de datos.
- `handlers/states.py`: guarda los estados usados por las conversaciones paso a paso.
- `handlers/helpers.py`: guarda funciones de apoyo para formatos, emojis y textos reutilizables.
- `database/`: contiene toda la logica relacionada con SQLite.
- `database/connection.py`: crea la carpeta `datos`, define la ruta de la base de datos y crea las tablas.
- `database/usuarios.py`: maneja datos de usuarios.
- `database/gastos.py`: maneja datos de gastos.
- `database/ingresos.py`: maneja ingresos extra.
- `database/limites.py`: maneja limites diarios y meses con registros.

## Instalacion

1. Instala Python.

2. Instala las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

3. Crea un archivo llamado `.env` en la raiz del proyecto.

4. Agrega la configuracion:

```env
TOKEN=tu_token_de_telegram
CONTRASENA=proyecto2026
HORA_RECORDATORIO=20:00
```

El `TOKEN` es obligatorio. Se obtiene creando un bot con BotFather en Telegram.
La `CONTRASENA` es la clave que una persona debe escribir para poder registrarse en el bot.

`HORA_RECORDATORIO` esta definida en la configuracion, pero el proyecto actual no tiene activo un recordatorio automatico.

## Como ejecutar el bot

Ejecuta:

```bash
python main.py
```

Si la configuracion es correcta, el bot queda encendido y esperando mensajes en Telegram.

Para detenerlo, presiona `Ctrl + C` en la terminal.

## Primer uso en Telegram

1. Abre el chat con el bot.
2. Escribe `/start`.
3. Ingresa la contrasena.
4. Escribe tu nombre.
5. Escribe tu ingreso mensual fijo.
6. Confirma la informacion con `SI`.

Despues del registro ya puedes usar los demas comandos.

## Comandos disponibles

### Registros

- `/gasto`: registra un gasto paso a paso.
- `/extra`: registra un ingreso extra paso a paso.

### Consultas

- `/inicio`: muestra el resumen del mes actual.
- `/lista`: muestra la lista de gastos del mes actual.
- `/mes`: permite elegir un mes con registros y ver su resumen.

### Perfil y edicion

- `/ingreso [monto]`: cambia el ingreso mensual fijo.
- `/cambiar_nombre`: cambia el nombre del usuario.
- `/deshacer`: elimina el ultimo gasto registrado.

### Borrado

- `/borrar_todo`: elimina todos los datos del usuario despues de varias confirmaciones.
- `/reset`: hace lo mismo que `/borrar_todo`.

### Ayuda

- `/ayuda`: muestra la lista de comandos dentro de Telegram.

## Categorias de gastos

Cuando registras un gasto, el bot pide elegir una categoria:

1. Comida
2. Vivienda
3. Compras
4. Salud
5. Suscripciones
6. Otros

## Base de datos

El proyecto crea automaticamente una carpeta llamada `datos`.

Dentro de esa carpeta se guarda la base de datos:

```text
datos/gastos.db
```

La base de datos tiene estas tablas:

- `usuarios`: guarda el usuario, nombre, ingreso fijo y fecha de registro.
- `gastos`: guarda los gastos registrados.
- `ingresos_extra`: guarda ingresos extra del mes.
- `contador_prompts`: controla el limite diario de mensajes por usuario.

## Limites y alertas

- Cada usuario tiene un limite de 100 mensajes por dia.
- Cada mensaje tiene un limite aproximado de 4000 tokens.
- Si un gasto supera el 50% del ingreso mensual, el bot pide una confirmacion adicional.
- Si el usuario gasta el 80% o mas de su dinero disponible, el bot muestra una alerta.

## Despliegue

El bot se ejecuta como un proceso de fondo.

El comando principal del proyecto actual es:

```bash
python main.py
```

Si vas a desplegarlo en una plataforma como Render o Heroku, el proceso debe ejecutar ese comando.



