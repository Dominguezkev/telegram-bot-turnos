# Bot de Telegram para turnos y consultas

Bot para un negocio chico (acá, una peluquería de ejemplo) que atiende a los
clientes por Telegram: responde las consultas de siempre con botones, manda la
ubicación en un mapa y toma turnos paso a paso.

> 🚧 **Estado: Días 1 a 3 terminados.** Funcionan `/start`, el menú con botones,
> `/horarios`, `/precios`, `/ubicacion` (con mapa), `/ayuda` y el flujo de
> reserva con `ConversationHandler` (`/reservar` + `/cancelar`). Los turnos se
> guardan **en memoria** por ahora; el Día 5 pasan a SQLite.

## Qué hace ahora

- `/start`: saluda y muestra el menú (📅 Reservar turno · 🕒 Horarios · 💲 Precios · 📍 Ubicación).
- `/reservar`: guía al cliente paso a paso (nombre → servicio → día/hora).
  También se puede iniciar tocando **📅 Reservar turno** en el menú.
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
✅ Resumen del turno
```

- Los estados (`NOMBRE`, `SERVICIO`, `HORA`) los maneja un `ConversationHandler`.
- Lo que responde el cliente se guarda en `context.user_data`.
- `/cancelar` funciona en cualquier paso y `/start` también corta la reserva
  y vuelve al menú.
- **Los turnos viven en memoria**: si el bot se reinicia, se pierden. Pasarlos
  a SQLite es el paso siguiente.

> 💡 El botón del menú entra al mismo flujo que `/reservar` mediante un
> `CallbackQueryHandler` como `entry_point` de la conversación.

## Personalizarlo para otro negocio

Casi todo está en [`textos.py`](textos.py): nombre, horarios, precios,
dirección y coordenadas. Para las coordenadas, abrí Google Maps, hacé clic
derecho sobre el local → "¿Qué hay aquí?" y copiá los dos números en
`LATITUD` y `LONGITUD`.

Después, en [`bot.py`](bot.py), cambiá las etiquetas de los botones si querés
otros rubros (por ejemplo "🛠 Servicios" en vez de "💲 Precios").

## Estructura

```text
telegram-bot-turnos/
├── bot.py            # handlers, teclados, conversación y arranque
├── config.py         # lee TOKEN desde .env y falla con un mensaje claro
├── textos.py         # textos y datos del negocio (editar acá)
├── .env.example      # plantilla del .env
├── requirements.txt
└── tests/
    └── test_bot.py   # tests de textos, botones, mapa y flujo de reserva
```

## Tests

No necesitan token ni conexión:

```bash
python tests/test_bot.py
```

## Seguridad

| Medida | Qué hace |
|---|---|
| Token en `.env` | Ni en el código ni en GitHub; `.env` está ignorado |
| Logs sin token | `httpx` bajado a WARNING: sus URLs incluyen el token |
| Error controlado | El usuario ve un mensaje genérico, el detalle va al log |
| Opción inválida | Un botón viejo no rompe nada: se muestra el menú |
| `/revoke` documentado | Si el token se filtra, se regenera en BotFather |

## Próximos pasos

1. Día 4: validar la fecha (formato correcto y que no sea del pasado) y volver
   a preguntar si está mal.
2. Día 5: guardar los turnos en SQLite y evitar dos reservas en el mismo horario.
3. Día 6-7: avisarle al dueño por Telegram cuando entra un turno nuevo.
4. Día 8-9: `/turnos` solo para el dueño (verificando su ID).
5. Día 10-12: logging en archivo, despliegue en Railway o Render con el token
   como variable de entorno.
