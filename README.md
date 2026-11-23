# Bot de Telegram para turnos y consultas

Bot para un negocio chico (acá, una peluquería de ejemplo) que atiende a los
clientes por Telegram: responde las consultas de siempre con botones, manda la
ubicación en un mapa y, en la próxima etapa, toma turnos paso a paso.

> 🚧 **Estado: Día 1 y 2 terminados.** Ya funcionan `/start`, el menú con
> botones, `/horarios`, `/precios`, `/ubicacion` y `/ayuda`. El flujo de reserva
> con `ConversationHandler` es el paso siguiente.

## Qué hace ahora

- `/start`: saluda y muestra el menú (🕒 Horarios · 💲 Precios · 📍 Ubicación).
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
├── bot.py            # handlers, teclados y arranque del bot
├── config.py         # lee TOKEN desde .env y falla con un mensaje claro
├── textos.py         # textos y datos del negocio (editar acá)
├── .env.example      # plantilla del .env
├── requirements.txt
└── tests/
    └── test_bot.py   # tests de textos, botones y coordenadas
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

## Próximos pasos (Día 3 en adelante)

1. Flujo de reserva con `ConversationHandler`: nombre → servicio → día/hora.
2. Guardar turnos en SQLite y evitar dos reservas en el mismo horario.
3. Avisarle al dueño por Telegram cuando entra un turno nuevo.
4. `/cancelar`, `/turnos` (solo para el dueño) y tests de la lógica de turnos.
5. Despliegue en Railway o Render con el token como variable de entorno.
