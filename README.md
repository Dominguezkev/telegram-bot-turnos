# Bot de Telegram para turnos y consultas

Bot para un negocio chico (acá, una peluquería de ejemplo) que atiende a los
clientes por Telegram: responde las consultas de siempre con botones, manda la
ubicación en un mapa y toma turnos paso a paso.

> 🚧 **Estado: Días 1 a 5 terminados.** Funcionan `/start`, el menú con botones,
> `/horarios`, `/precios`, `/ubicacion` (con mapa), `/ayuda` y el flujo de
> reserva con `ConversationHandler` (`/reservar` + `/cancelar`). Las fechas se
> validan contra el calendario y el horario de atención, y los turnos se
> guardan en **SQLite**, que rechaza dos reservas en el mismo horario.

## Qué hace ahora

- `/start`: saluda y muestra el menú (📅 Reservar turno · 🕒 Horarios · 💲 Precios · 📍 Ubicación).
- `/reservar`: guía al cliente paso a paso (nombre → servicio → día/hora).
  También se puede iniciar tocando **📅 Reservar turno** en el menú.
- Valida la fecha: formato, que no sea pasada, que no sea domingo y que esté
  dentro del horario de atención (sábados hasta más temprano). Si está mal,
  vuelve a preguntar sin perder lo ya cargado.
- Guarda el turno en `turnos.db`. Si el horario ya está ocupado, muestra las
  horas tomadas de ese día y vuelve a preguntar.
- `/cancelar`: corta la reserva en cualquier paso.
- `/horarios`, `/precios`, `/ubicacion`: responden también como comandos sueltos.
- `/ubicacion` manda la dirección y después el mapa con `reply_location`.
- `/ayuda`: lista los comandos disponibles.
- Registra los comandos en el menú de Telegram (el que aparece al escribir `/`).
- Si algo falla, el usuario recibe un mensaje amable y el error queda en el log.

## Requisitos

- Python 3.10 o superior (probado con 3.14).
- Un token de Telegram: hablá con [@BotFather](https://t.me/BotFather),
  mandá `/newbot`, elegí nombre y usuario, y copiá el token.

## Instalación

Desde la carpeta del proyecto (`telegram-bot-turnos`):

```bash
python -m venv venv
source venv/bin/activate          # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configurar el token

```bash
cp .env.example .env
```

Abrí `.env` y reemplazá el valor de `TOKEN` por el de BotFather:

```dotenv
TOKEN=123456789:AAH...
```

El `.env` está en `.gitignore`: nunca se sube al repo. Si lo subiste por error,
regenerá el token en BotFather con `/revoke` (borrar el archivo no alcanza,
queda en el historial de git).

### Correr el bot

```bash
python bot.py
```

En Windows: `venv\Scripts\python bot.py`.

Vas a ver algo así:

```text
2026-11-23 18:30:00 - __main__ - INFO - Bot iniciado. Abrí Telegram y mandá /start.
```

Abrí el bot en Telegram, mandá `/start` y probá los botones. `Ctrl+C` lo frena.

## Flujo de reserva

```
/reservar (o botón 📅)
   ↓
¿Cómo te llamás?           → el cliente escribe su nombre
   ↓
¿Qué servicio querés?      → botones: Corte / Corte + barba / Color / Peinado
   ↓
¿Qué día y hora?           → el cliente escribe, ej: 25/11 15:00
   ↓
validaciones.py revisa formato, fecha futura, domingo y horario
   ↓
   ├── si está mal → mensaje de error y vuelve a preguntar (mismo estado HORA)
   ↓
database.py guarda el turno (restricción UNIQUE)
   ├── si está ocupado → muestra las horas tomadas y vuelve a preguntar
   ↓
✅ Resumen del turno con la fecha completa
```

- Los estados (`NOMBRE`, `SERVICIO`, `HORA`) los maneja un `ConversationHandler`.
- Lo que responde el cliente se guarda en `context.user_data`.
- Si la fecha es inválida, `confirmar` devuelve `HORA` otra vez: no se pierden
  el nombre ni el servicio.
- Acepta `25/11 15:00` y `25/11/2026 15:00`. Sin año, usa el año actual (y en
  diciembre entiende que un enero es del año siguiente).
- `/cancelar` funciona en cualquier paso y `/start` también corta la reserva
  y vuelve al menú.
- **Los turnos se guardan en `turnos.db`**: sobreviven a los reinicios del bot.

> 💡 El botón del menú entra al mismo flujo que `/reservar` mediante un
> `CallbackQueryHandler` como `entry_point` de la conversación.

## Validación de fechas

La lógica vive en [`validaciones.py`](validaciones.py), sin nada de Telegram,
para poder testearla con una fecha fija:

| Regla | Ejemplo rechazado |
|---|---|
| Formato `dd/mm hh:mm` o `dd/mm/aaaa hh:mm` | `mañana`, `31/02 15:00` |
| Tiene que ser futura | hoy a las 9:00 si ya son las 10:00 |
| Domingos cerrado | domingo 29/11 15:00 |
| Lunes a viernes 9:00–19:00 | 21:00 u 8:59 |
| Sábados 9:00–14:00 | sábado 15:00 |

Los horarios están en `textos.py` (`HORARIO_SEMANA` y `HORARIO_SABADO`) y se
usan tanto para el texto de `/horarios` como para la validación.

## Base de datos

Los turnos se guardan en `turnos.db`, un archivo SQLite junto al bot:

| Columna | Tipo | Para qué |
|---|---|---|
| `id` | INTEGER | Clave primaria autoincremental |
| `chat_id` | INTEGER | Chat de Telegram del cliente |
| `nombre` | TEXT | Nombre que escribió |
| `servicio` | TEXT | Corte, Color, etc. |
| `fecha_hora` | TEXT | `2026-11-25 15:00`, con **UNIQUE** |

La restricción `UNIQUE` es la que impide dos turnos a la misma hora, incluso
si dos clientes confirman al mismo tiempo. `guardar_turno()` no revisa "a
mano": intenta insertar y, si SQLite lanza `IntegrityError`, devuelve `False`.

`horarios_ocupados(dia)` consulta las horas tomadas de un día y el bot las
muestra cuando rechaza un horario.

El archivo está en `.gitignore` porque tiene datos de clientes:

```bash
# ver los turnos cargados
sqlite3 turnos.db "SELECT * FROM turnos ORDER BY fecha_hora;"
```

> ⚠️ En Railway o Render el disco se puede borrar en cada reinicio. En el
> despliegue hay que montar un volumen persistente o pasar a PostgreSQL.

## Personalizarlo para otro negocio

Casi todo está en [`textos.py`](textos.py): nombre, horarios, precios,
dirección y coordenadas. Los horarios son tuplas (`HORARIO_SEMANA`,
`HORARIO_SABADO`) para que el texto de `/horarios` y la validación de turnos
usen los mismos números. Para las coordenadas, abrí Google Maps, hacé clic
derecho sobre el local → "¿Qué hay aquí?" y copiá los dos números en
`LATITUD` y `LONGITUD`.

Después, en [`bot.py`](bot.py), cambiá las etiquetas de los botones si querés
otros rubros (por ejemplo "🛠 Servicios" en vez de "💲 Precios").

## Estructura

```text
telegram-bot-turnos/
├── bot.py              # handlers, teclados, conversación y arranque
├── config.py           # lee TOKEN desde .env y falla con un mensaje claro
├── database.py         # SQLite: tabla, guardar turno y horarios ocupados
├── textos.py           # textos y datos del negocio (editar acá)
├── validaciones.py     # validación de fechas/horarios, sin Telegram
├── turnos.db           # se crea al arrancar (ignorado por git)
├── .env.example        # plantilla del .env
├── requirements.txt
├── requirements-dev.txt
└── tests/
    ├── test_bot.py           # textos, botones, mapa y flujo de reserva
    ├── test_database.py      # duplicados, horarios ocupados y SQL injection
    └── test_validaciones.py  # fechas válidas, pasadas, domingos y horarios
```

## Tests

No necesitan token ni conexión. Con pytest:

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

`test_database.py` usa los fixtures `tmp_path` y `monkeypatch` de pytest (base
temporal, sin tocar `turnos.db`), así que ese archivo necesita pytest. Los
otros dos también se pueden correr sin pytest:

```bash
python tests/test_bot.py
python tests/test_validaciones.py
```

## Seguridad

| Medida | Qué hace |
|---|---|
| Token en `.env` | Ni en el código ni en GitHub; `.env` está ignorado |
| Logs sin token | `httpx` bajado a WARNING: sus URLs incluyen el token |
| SQL parametrizado | Los valores van con `?`: un nombre con comillas no altera la base |
| Base fuera de git | `turnos.db` tiene datos de clientes y está ignorado |
| Error controlado | El usuario ve un mensaje genérico, el detalle va al log |
| Opción inválida | Un botón viejo no rompe nada: se muestra el menú |
| `/revoke` documentado | Si el token se filtra, se regenera en BotFather |

## Próximos pasos

1. Día 6-7: avisarle al dueño por Telegram cuando entra un turno nuevo.
2. Día 8-9: `/turnos` solo para el dueño (verificando su ID).
3. Día 10-12: logging en archivo, despliegue en Railway o Render con el token
   como variable de entorno y un volumen para `turnos.db`.
