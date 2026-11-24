# tests/test_bot.py
"""Tests offline: textos, botones, mapa y flujo de reserva.

No necesitan token ni conexión: los mensajes de Telegram se simulan.

Correrlos desde la carpeta del proyecto:
    python tests/test_bot.py
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

# Permite importar bot.py y textos.py desde cualquier carpeta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram import ReplyKeyboardRemove                       # noqa: E402
from telegram.error import TelegramError                       # noqa: E402
from telegram.ext import (                                      # noqa: E402
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)

import bot        # noqa: E402
import textos     # noqa: E402
from validaciones import validar_fecha                          # noqa: E402

# "Ahora" fijo para los tests que pasan por bot.confirmar.
AHORA = datetime(2026, 11, 24, 10, 0)


class MensajeFalso:
    """Anota lo que el handler intenta mandar, sin hablar con Telegram."""

    def __init__(self, texto=None):
        self.text = texto
        self.textos = []
        self.ubicaciones = []

    async def reply_text(self, texto, reply_markup=None):
        self.textos.append((texto, reply_markup))

    async def reply_location(self, latitude, longitude):
        self.ubicaciones.append((latitude, longitude))


class QueryFalsa:
    """Simula el toque de un botón."""

    def __init__(self, data):
        self.data = data
        self.answered = False
        self.editados = []
        self.message = MensajeFalso()

    async def answer(self):
        self.answered = True

    async def edit_message_text(self, texto, reply_markup=None):
        self.editados.append((texto, reply_markup))


def botones(teclado):
    """Aplana las filas del teclado en una sola lista de botones."""
    return [boton for fila in teclado.inline_keyboard for boton in fila]


def update_de(texto):
    """Arma un update como el que llega cuando el cliente escribe."""
    mensaje = MensajeFalso(texto)
    return SimpleNamespace(
        message=mensaje,
        effective_message=mensaje,
        effective_chat=SimpleNamespace(id=123),
        effective_user=SimpleNamespace(full_name="Ana Pérez", username="ana"),
    ), mensaje


# --- Menú y consultas -----------------------------------------------------

def test_menu_tiene_reservar_y_consultas():
    datos = [b.callback_data for b in botones(bot.teclado_menu())]
    assert datos == ["reservar", "horarios", "precios", "ubicacion"]


def test_cada_boton_del_menu_tiene_respuesta():
    for boton in botones(bot.teclado_menu()):
        if boton.callback_data in ("reservar", "ubicacion"):
            continue
        assert textos.CONSULTAS[boton.callback_data].strip()


def test_volver_apunta_al_menu():
    datos = [b.callback_data for b in botones(bot.teclado_volver())]
    assert datos == ["menu"]


def test_ubicacion_menciona_la_direccion():
    assert textos.DIRECCION in textos.UBICACION_TEXTO


def test_coordenadas_dentro_de_rango():
    # Un error típico de copy/paste: pegar latitud y longitud al revés o
    # dejar las de ejemplo del Obelisco para un local en otra ciudad.
    assert -90 <= textos.LATITUD <= 90
    assert -180 <= textos.LONGITUD <= 180
    assert (textos.LATITUD, textos.LONGITUD) != (0, 0)


def test_ayuda_lista_todos_los_comandos():
    for comando in ("/start", "/reservar", "/cancelar", "/horarios",
                    "/precios", "/ubicacion", "/ayuda"):
        assert comando in textos.AYUDA


def test_no_quedan_marcadores_sin_completar():
    for nombre in ("SALUDO", "HORARIOS", "PRECIOS", "UBICACION_TEXTO",
                   "AYUDA", "PREGUNTA_NOMBRE", "PREGUNTA_SERVICIO",
                   "PREGUNTA_HORA", "CONFIRMACION", "ERROR_FECHA_FORMATO",
                   "ERROR_FECHA_PASADA", "ERROR_DOMINGO",
                   "ERROR_FUERA_DE_HORARIO", "ERROR_NOMBRE",
                   "TURNO_OCUPADO", "AVISO_DUENO"):
        valor = getattr(textos, nombre)
        assert "TODO" not in valor and "tu_" not in valor


def test_comando_ubicacion_manda_texto_y_mapa():
    mensaje = MensajeFalso()
    update = SimpleNamespace(effective_message=mensaje)

    asyncio.run(bot.ubicacion(update, None))

    assert mensaje.textos[0][0] == textos.UBICACION_TEXTO
    assert mensaje.ubicaciones == [(textos.LATITUD, textos.LONGITUD)]


def test_boton_ubicacion_contesta_y_manda_mapa():
    query = QueryFalsa("ubicacion")

    asyncio.run(bot.boton(SimpleNamespace(callback_query=query), None))

    assert query.answered, "si no se hace answer() Telegram deja la ruedita girando"
    assert query.editados[0][0] == textos.UBICACION_TEXTO
    assert query.message.ubicaciones == [(textos.LATITUD, textos.LONGITUD)]


def test_boton_horarios_responde_y_ofrece_volver():
    query = QueryFalsa("horarios")

    asyncio.run(bot.boton(SimpleNamespace(callback_query=query), None))

    assert query.editados[0][0] == textos.HORARIOS
    datos = [b.callback_data for b in botones(query.editados[0][1])]
    assert datos == ["menu"]


def test_boton_viejo_no_rompe_y_vuelve_al_menu():
    query = QueryFalsa("promo-que-ya-no-existe")

    asyncio.run(bot.boton(SimpleNamespace(callback_query=query), None))

    assert query.editados[0][0] == textos.OPCION_INVALIDA
    datos = [b.callback_data for b in botones(query.editados[0][1])]
    assert datos == ["reservar", "horarios", "precios", "ubicacion"]


# --- Reserva --------------------------------------------------------------

def test_teclado_servicios_usa_los_servicios_del_negocio():
    teclado = bot.teclado_servicios()
    planos = [b.text for fila in teclado.keyboard for b in fila]

    assert planos == textos.SERVICIOS
    assert teclado.one_time_keyboard is True
    assert teclado.resize_keyboard is True
    assert len(teclado.keyboard[0]) <= 2, "más de dos botones por fila se ve apretado"


def test_flujo_completo_de_reserva():
    context = SimpleNamespace(user_data={})

    # /reservar → pregunta nombre
    update, mensaje = update_de("/reservar")
    assert asyncio.run(bot.reservar(update, context)) == bot.NOMBRE
    assert textos.PREGUNTA_NOMBRE in mensaje.textos[0][0]

    # nombre → pregunta servicio y muestra botones
    update, mensaje = update_de("Ana")
    assert asyncio.run(bot.pedir_servicio(update, context)) == bot.SERVICIO
    assert context.user_data["nombre"] == "Ana"
    assert mensaje.textos[0][0] == textos.PREGUNTA_SERVICIO
    assert mensaje.textos[0][1] is not None

    # servicio → pide fecha y saca los botones
    update, mensaje = update_de("Corte")
    assert asyncio.run(bot.pedir_hora(update, context)) == bot.HORA
    assert context.user_data["servicio"] == "Corte"
    assert isinstance(mensaje.textos[0][1], ReplyKeyboardRemove)

    # fecha → valida, guarda, confirma y termina
    update, mensaje = update_de("25/11 15:00")
    guardados = []

    def guardar_falso(chat_id, nombre, servicio, fecha):
        guardados.append((chat_id, nombre, servicio, fecha))
        return True

    aviso = AsyncMock()
    with patch.object(
        bot, "validar_fecha", lambda texto: validar_fecha(texto, AHORA)
    ), patch.object(bot, "guardar_turno", guardar_falso), patch.object(
        bot, "avisar_dueno", aviso
    ):
        estado = asyncio.run(bot.confirmar(update, context))
    assert estado == ConversationHandler.END
    confirmacion = mensaje.textos[0][0]
    assert "Ana" in confirmacion
    assert "Corte" in confirmacion
    assert "25/11/2026 15:00" in confirmacion
    assert guardados == [(123, "Ana", "Corte", datetime(2026, 11, 25, 15, 0))]
    assert aviso.await_args.args[1:] == (
        "Ana",
        "Corte",
        datetime(2026, 11, 25, 15, 0),
        "Ana Pérez (@ana)",
    )
    assert context.user_data == {}, "no hay que dejar datos de la reserva vieja"


def test_nombre_invalido_vuelve_a_preguntar():
    context = SimpleNamespace(user_data={})
    update, mensaje = update_de("A")

    estado = asyncio.run(bot.pedir_servicio(update, context))

    assert estado == bot.NOMBRE, "tiene que quedarse esperando otro nombre"
    assert mensaje.textos[0][0].startswith("❌")
    assert "nombre" in mensaje.textos[0][0].lower()
    assert "nombre" not in context.user_data


def test_nombre_valido_se_guarda_limpio():
    context = SimpleNamespace(user_data={})
    update, _ = update_de("  Ana   María ")

    estado = asyncio.run(bot.pedir_servicio(update, context))

    assert estado == bot.SERVICIO
    assert context.user_data["nombre"] == "Ana María"


def test_confirmar_rechaza_horario_ocupado_y_muestra_cuales():
    context = SimpleNamespace(user_data={"nombre": "Ana", "servicio": "Corte"})
    update, mensaje = update_de("25/11 15:00")

    with patch.object(
        bot, "validar_fecha", lambda texto: validar_fecha(texto, AHORA)
    ), patch.object(bot, "guardar_turno", lambda *args: False), patch.object(
        bot, "horarios_ocupados", lambda fecha: ["15:00", "16:30"]
    ):
        estado = asyncio.run(bot.confirmar(update, context))

    respuesta = mensaje.textos[0][0]
    assert estado == bot.HORA, "tiene que volver a pedir otro horario"
    assert "ocupado" in respuesta.lower()
    assert "25/11" in respuesta
    assert "15:00, 16:30" in respuesta
    assert context.user_data == {"nombre": "Ana", "servicio": "Corte"}


def test_confirmar_con_fecha_invalida_vuelve_a_preguntar():
    context = SimpleNamespace(user_data={"nombre": "Ana", "servicio": "Corte"})
    update, mensaje = update_de("asdf")

    estado = asyncio.run(bot.confirmar(update, context))

    assert estado == bot.HORA, "tiene que quedarse esperando otra fecha"
    assert mensaje.textos[0][0].startswith("❌")
    assert "25/11" in mensaje.textos[0][0], "el error tiene que mostrar el formato"
    assert context.user_data == {"nombre": "Ana", "servicio": "Corte"}


def test_cancelar_limpia_los_datos():
    context = SimpleNamespace(user_data={"nombre": "Ana"})
    update, mensaje = update_de("/cancelar")

    assert asyncio.run(bot.cancelar(update, context)) == ConversationHandler.END
    assert context.user_data == {}
    assert mensaje.textos[0][0] == textos.RESERVA_CANCELADA


def test_boton_reservar_inicia_el_flujo():
    query = QueryFalsa("reservar")
    update = SimpleNamespace(callback_query=query, effective_message=query.message)

    estado = asyncio.run(bot.reservar_boton(update, SimpleNamespace(user_data={})))

    assert query.answered
    assert estado == bot.NOMBRE
    assert query.editados[0][0] == textos.RESERVA_INTRO
    assert textos.PREGUNTA_NOMBRE in query.message.textos[0][0]


def test_cancelar_fuera_de_reserva_no_rompe():
    mensaje = MensajeFalso()

    asyncio.run(bot.cancelar_fuera(SimpleNamespace(effective_message=mensaje), None))

    assert mensaje.textos[0][0] == textos.SIN_RESERVA


# --- Aviso al dueño -------------------------------------------------------

def test_aviso_al_dueno_manda_chat_id_y_detalle():
    enviar = AsyncMock()
    context = SimpleNamespace(bot=SimpleNamespace(send_message=enviar))

    with patch.object(bot, "OWNER_ID", 999):
        asyncio.run(bot.avisar_dueno(
            context,
            "Ana",
            "Corte",
            datetime(2026, 11, 25, 15, 0),
            "Ana Pérez (@ana)",
        ))

    enviar.assert_awaited_once()
    kwargs = enviar.await_args.kwargs
    assert kwargs["chat_id"] == 999
    assert "Ana" in kwargs["text"]
    assert "Corte" in kwargs["text"]
    assert "25/11/2026 15:00" in kwargs["text"]
    assert "@ana" in kwargs["text"]


def test_aviso_al_dueno_no_explota_si_telegram_falla():
    enviar = AsyncMock(side_effect=TelegramError("bot was blocked by the user"))
    context = SimpleNamespace(bot=SimpleNamespace(send_message=enviar))

    with patch.object(bot, "OWNER_ID", 999), patch.object(bot.logger, "error"):
        asyncio.run(bot.avisar_dueno(
            context,
            "Ana",
            "Corte",
            datetime(2026, 11, 25, 15, 0),
            "Ana Pérez",
        ))

    enviar.assert_awaited_once()


def test_sin_owner_id_no_intenta_avisar():
    enviar = AsyncMock()
    context = SimpleNamespace(bot=SimpleNamespace(send_message=enviar))

    with patch.object(bot, "OWNER_ID", None), patch.object(bot.logger, "warning"):
        asyncio.run(bot.avisar_dueno(
            context,
            "Ana",
            "Corte",
            datetime(2026, 11, 25, 15, 0),
            "Ana Pérez",
        ))

    enviar.assert_not_awaited()


def test_si_falla_el_aviso_el_cliente_igual_recibe_la_confirmacion():
    context = SimpleNamespace(
        user_data={"nombre": "Ana", "servicio": "Corte"},
        bot=SimpleNamespace(
            send_message=AsyncMock(side_effect=TelegramError("bloqueado"))
        ),
    )
    update, mensaje = update_de("25/11 15:00")

    with patch.object(bot, "OWNER_ID", 999), patch.object(
        bot.logger, "error"
    ), patch.object(
        bot, "validar_fecha", lambda texto: validar_fecha(texto, AHORA)
    ), patch.object(bot, "guardar_turno", lambda *args: True):
        estado = asyncio.run(bot.confirmar(update, context))

    assert estado == ConversationHandler.END
    assert "Turno reservado" in mensaje.textos[0][0]
    assert context.user_data == {}
    context.bot.send_message.assert_awaited_once()


# --- Errores no manejados -------------------------------------------------

def test_error_handler_avisa_al_usuario():
    mensaje = MensajeFalso()
    update = SimpleNamespace(effective_message=mensaje)

    with patch.object(bot.logger, "error"):
        asyncio.run(bot.manejar_error(update, SimpleNamespace(error=RuntimeError("boom"))))

    assert mensaje.textos[0][0] == textos.MENSAJE_ERROR


# --- Cableado del ConversationHandler -------------------------------------

def test_conversacion_entra_por_comando_y_por_boton():
    tipos = [type(h) for h in bot.reserva.entry_points]
    assert CommandHandler in tipos, "falta /reservar"
    assert CallbackQueryHandler in tipos, "falta el botón del menú"


def test_conversacion_tiene_fallbacks_de_salida():
    comandos = set()
    for handler in bot.reserva.fallbacks:
        comandos |= set(getattr(handler, "commands", set()))

    assert {"cancelar", "start"} <= comandos, "sin salida, el cliente queda atrapado"


def test_la_conversacion_se_registra_antes_del_boton_generico():
    app = bot.crear_app("123456789:AAHfake-token-para-probar")
    handlers = app.handlers[0]

    indice_conversacion = next(
        i for i, h in enumerate(handlers) if isinstance(h, ConversationHandler)
    )
    indice_callback = next(
        i for i, h in enumerate(handlers) if isinstance(h, CallbackQueryHandler)
    )

    # Si el genérico va primero, se come el toque de "reservar".
    assert indice_conversacion < indice_callback


def test_la_app_registra_el_manejador_de_errores():
    app = bot.crear_app("123456789:AAHfake-token-para-probar")

    assert bot.manejar_error in app.error_handlers


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for prueba in pruebas:
        try:
            prueba()
            ok += 1
            print(f"✔ {prueba.__name__}")
        except AssertionError as e:
            print(f"❌ FALLÓ: {prueba.__name__} ({e})")
    print(f"\n{'✅' if ok == len(pruebas) else '❌'} {ok} de {len(pruebas)} tests OK")
    sys.exit(0 if ok == len(pruebas) else 1)
