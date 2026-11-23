"""Bot de Telegram para una peluquería — Día 1 y 2 del proyecto.

Hoy hace tres cosas:
- /start muestra un menú con botones.
- Responde horarios, precios y ubicación.
- Manda el mapa del local con reply_location.

Ejecutar desde la carpeta del proyecto:
    python bot.py
"""
import logging
import sys
from pathlib import Path

# Permite importar config.py y textos.py aunque se ejecute desde otra carpeta.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import textos
from config import obtener_token

logger = logging.getLogger(__name__)


# --- Teclados -------------------------------------------------------------

def teclado_menu() -> InlineKeyboardMarkup:
    """Botones que acompañan al saludo de /start."""
    filas = [
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


# --- Comandos -------------------------------------------------------------

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


# --- Botones --------------------------------------------------------------

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


# --- Arranque -------------------------------------------------------------

async def registrar_comandos(app: Application) -> None:
    """Carga el menú de comandos que Telegram muestra al escribir '/'."""
    await app.bot.set_my_commands([
        ("start", "Empezar / ver el menú"),
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


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # httpx registra las URLs completas de las peticiones y la URL de Telegram
    # incluye el token: en INFO lo estaríamos filtrando en los logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    app = (
        Application.builder()
        .token(obtener_token())
        .post_init(registrar_comandos)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("horarios", horarios))
    app.add_handler(CommandHandler("precios", precios))
    app.add_handler(CommandHandler("ubicacion", ubicacion))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CallbackQueryHandler(boton))
    app.add_error_handler(manejar_error)

    logger.info("Bot iniciado. Abrí Telegram y mandá /start. (Ctrl+C para frenar)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
