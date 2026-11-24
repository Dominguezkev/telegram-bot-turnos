"""Bot de Telegram para una peluquería — Días 1 a 5 del proyecto.

Hoy hace cuatro cosas:
- /start muestra un menú con botones.
- Responde horarios, precios y ubicación (también como comandos).
- Manda el mapa del local con reply_location.
- /reservar guía al cliente paso a paso: nombre → servicio → día/hora,
  validando la fecha y guardando el turno en SQLite.

La base de datos impide dos turnos en el mismo horario (restricción UNIQUE).

Ejecutar desde la carpeta del proyecto:
    python bot.py
"""
import logging
import sys
import warnings
from pathlib import Path

# Permite importar config.py y textos.py aunque se ejecute desde otra carpeta.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.warnings import PTBUserWarning
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import textos
from config import obtener_token
from database import guardar_turno, horarios_ocupados, init_db
from validaciones import validar_fecha

logger = logging.getLogger(__name__)

# Estados de la conversación de reserva.
NOMBRE, SERVICIO, HORA = range(3)

# Solo texto: los comandos (/cancelar, /start) van por los fallbacks.
TEXTO = filters.TEXT & ~filters.COMMAND


# --- Teclados -------------------------------------------------------------

def teclado_menu() -> InlineKeyboardMarkup:
    """Botones que acompañan al saludo de /start."""
    filas = [
        [InlineKeyboardButton("📅 Reservar turno", callback_data="reservar")],
        [
            InlineKeyboardButton("🕒 Horarios", callback_data="horarios"),
            InlineKeyboardButton("💲 Precios", callback_data="precios"),
        ],
        [InlineKeyboardButton("📍 Ubicación", callback_data="ubicacion")],
    ]
    return InlineKeyboardMarkup(filas)


def teclado_volver() -> InlineKeyboardMarkup:
    """Botón para que el usuario vuelva al menú después de una consulta."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu")]]
    )


def teclado_servicios() -> ReplyKeyboardMarkup:
    """Botones con los servicios, de a dos por fila."""
    filas = [
        textos.SERVICIOS[i:i + 2]
        for i in range(0, len(textos.SERVICIOS), 2)
    ]
    return ReplyKeyboardMarkup(
        filas, one_time_keyboard=True, resize_keyboard=True
    )


# --- Consultas ------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saluda y muestra el menú de consultas."""
    await update.effective_message.reply_text(
        textos.SALUDO, reply_markup=teclado_menu()
    )


async def horarios(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        textos.HORARIOS, reply_markup=teclado_volver()
    )


async def precios(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        textos.PRECIOS, reply_markup=teclado_volver()
    )


async def ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manda la dirección en texto y después el mapa como ubicación."""
    mensaje = update.effective_message
    await mensaje.reply_text(textos.UBICACION_TEXTO, reply_markup=teclado_volver())
    await mensaje.reply_location(
        latitude=textos.LATITUD,
        longitude=textos.LONGITUD,
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        textos.AYUDA, reply_markup=teclado_menu()
    )


# --- Reserva de turnos (por ahora, en memoria) ----------------------------

async def reservar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 0: arranca la reserva y pregunta el nombre."""
    # Si había una reserva abandonada, no mezclamos datos viejos.
    context.user_data.clear()
    await update.effective_message.reply_text(
        textos.PREGUNTA_NOMBRE, reply_markup=ReplyKeyboardRemove()
    )
    return NOMBRE


async def reservar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """El botón del menú entra al mismo flujo que /reservar."""
    query = update.callback_query
    await query.answer()
    # Sacamos los botones del menú para que no queden a mano.
    await query.edit_message_text(textos.RESERVA_INTRO)
    return await reservar(update, context)


async def pedir_servicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 1: guarda el nombre y ofrece los servicios con botones."""
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text(
        textos.PREGUNTA_SERVICIO, reply_markup=teclado_servicios()
    )
    return SERVICIO


async def pedir_hora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 2: guarda el servicio y pide día y hora."""
    context.user_data["servicio"] = update.message.text.strip()
    await update.message.reply_text(
        textos.PREGUNTA_HORA,
        reply_markup=ReplyKeyboardRemove(),  # saca los botones de servicios
    )
    return HORA


async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 3: valida la fecha, muestra el resumen y cierra la conversación."""
    fecha, error = validar_fecha(update.message.text)

    if error:
        # Devolvemos el MISMO estado para que el ConversationHandler vuelva a
        # esperar la fecha, sin perder el nombre ni el servicio ya elegidos.
        await update.message.reply_text(
            f"❌ {error}\n\nProbá de nuevo (o mandá /cancelar).",
            reply_markup=ReplyKeyboardRemove(),
        )
        return HORA

    datos = context.user_data
    guardado = guardar_turno(
        update.effective_chat.id,
        datos["nombre"],
        datos["servicio"],
        fecha,
    )

    if not guardado:
        # La base rechazó el turno por el UNIQUE: mostramos qué horas quedan
        # tomadas ese día y volvemos al mismo estado para elegir otra.
        horas = ", ".join(horarios_ocupados(fecha))
        await update.message.reply_text(
            textos.TURNO_OCUPADO.format(
                dia=fecha.strftime("%d/%m"), horas=horas
            ),
            reply_markup=ReplyKeyboardRemove(),
        )
        return HORA

    await update.message.reply_text(
        textos.CONFIRMACION.format(
            nombre=datos["nombre"],
            servicio=datos["servicio"],
            cuando=fecha.strftime("%d/%m/%Y %H:%M"),
        ),
        reply_markup=ReplyKeyboardRemove(),
    )
    datos.clear()
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sale de la reserva en cualquier paso."""
    context.user_data.clear()
    await update.effective_message.reply_text(
        textos.RESERVA_CANCELADA, reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def cancelar_fuera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cancelar cuando no hay ninguna reserva activa."""
    await update.effective_message.reply_text(
        textos.SIN_RESERVA, reply_markup=ReplyKeyboardRemove()
    )


async def salir_a_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Si mandan /start en medio de la reserva, la cortan y vuelven al menú."""
    context.user_data.clear()
    await update.effective_message.reply_text(
        f"{textos.RESERVA_INTERRUMPIDA}\n\n{textos.SALUDO}",
        reply_markup=teclado_menu(),
    )
    return ConversationHandler.END


# --- Botones de las consultas ---------------------------------------------

async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde según el botón que tocó el usuario."""
    query = update.callback_query

    # Obligatorio: le avisa a Telegram que recibimos el toque; si no, el
    # cliente ve la ruedita girando para siempre.
    await query.answer()

    if query.data == "menu":
        await query.edit_message_text(textos.SALUDO, reply_markup=teclado_menu())
        return

    if query.data == "ubicacion":
        await query.edit_message_text(
            textos.UBICACION_TEXTO, reply_markup=teclado_volver()
        )
        # La ubicación va en un mensaje aparte: Telegram no la muestra dentro
        # de un mensaje de texto común.
        await query.message.reply_location(
            latitude=textos.LATITUD,
            longitude=textos.LONGITUD,
        )
        return

    respuesta = textos.CONSULTAS.get(query.data)
    if respuesta is None:
        await query.edit_message_text(
            textos.OPCION_INVALIDA, reply_markup=teclado_menu()
        )
        return

    await query.edit_message_text(respuesta, reply_markup=teclado_volver())


# --- Conversación ---------------------------------------------------------

# El botón del menú entra con CallbackQueryHandler, pero los pasos son texto.
# PTB avisa que los callbacks no se rastrean "por mensaje" (per_message=False);
# es lo esperado acá porque dentro de la conversación no hay más callbacks.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="If 'per_message=False'",
        category=PTBUserWarning,
    )
    reserva = ConversationHandler(
        entry_points=[
            CommandHandler("reservar", reservar),
            # El ejercicio: el botón del menú inicia la misma conversación.
            CallbackQueryHandler(reservar_boton, pattern="^reservar$"),
        ],
        states={
            NOMBRE: [MessageHandler(TEXTO, pedir_servicio)],
            SERVICIO: [MessageHandler(TEXTO, pedir_hora)],
            HORA: [MessageHandler(TEXTO, confirmar)],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar),
            CommandHandler("start", salir_a_menu),
        ],
        name="reserva",
    )


# --- Arranque -------------------------------------------------------------

async def registrar_comandos(app: Application) -> None:
    """Carga el menú de comandos que Telegram muestra al escribir '/'."""
    await app.bot.set_my_commands([
        ("start", "Empezar / ver el menú"),
        ("reservar", "Sacar un turno paso a paso"),
        ("cancelar", "Cancelar una reserva a medias"),
        ("horarios", "Días y horas de atención"),
        ("precios", "Lista de precios"),
        ("ubicacion", "Dirección y mapa"),
        ("ayuda", "Qué puede hacer el bot"),
    ])


async def manejar_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra el error y avisa al usuario sin exponer detalles internos."""
    logger.error("Error procesando la actualización: %s", update, exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(textos.MENSAJE_ERROR)
        except Exception:  # pragma: no cover - si ni siquiera podemos avisar
            logger.exception("Tampoco se pudo avisar del error al usuario")


def crear_app(token: str) -> Application:
    """Arma la aplicación y registra todos los handlers."""
    app = (
        Application.builder()
        .token(token)
        .post_init(registrar_comandos)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("horarios", horarios))
    app.add_handler(CommandHandler("precios", precios))
    app.add_handler(CommandHandler("ubicacion", ubicacion))
    app.add_handler(CommandHandler("ayuda", ayuda))

    # La conversación va ANTES del CallbackQueryHandler genérico: si no, el
    # botón "reservar" lo atendería `boton` y la reserva nunca arrancaría.
    app.add_handler(reserva)
    # Fuera de una reserva, /cancelar no rompe: explica que no hay nada activo.
    app.add_handler(CommandHandler("cancelar", cancelar_fuera))

    app.add_handler(CallbackQueryHandler(boton))
    app.add_error_handler(manejar_error)
    return app


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # httpx registra las URLs completas de las peticiones y la URL de Telegram
    # incluye el token: en INFO lo estaríamos filtrando en los logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    init_db()  # crea turnos.db la primera vez
    app = crear_app(obtener_token())

    logger.info("Bot iniciado. Abrí Telegram y mandá /start. (Ctrl+C para frenar)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
