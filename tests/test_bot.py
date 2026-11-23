# tests/test_bot.py
"""Tests de la parte que no necesita Telegram: textos, botones y coordenadas.

Correrlos desde la carpeta del proyecto:
    python tests/test_bot.py
"""
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

# Permite importar bot.py y textos.py desde cualquier carpeta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bot        # noqa: E402
import textos     # noqa: E402


class MensajeFalso:
    """Anota lo que el handler intenta mandar, sin hablar con Telegram."""

    def __init__(self):
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


def test_menu_tiene_las_tres_consultas():
    datos = [b.callback_data for b in botones(bot.teclado_menu())]
    assert datos == ["horarios", "precios", "ubicacion"]


def test_cada_boton_del_menu_tiene_respuesta():
    for boton in botones(bot.teclado_menu()):
        if boton.callback_data == "ubicacion":
            assert textos.UBICACION_TEXTO.strip()
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
    for comando in ("/start", "/horarios", "/precios", "/ubicacion", "/ayuda"):
        assert comando in textos.AYUDA


def test_no_quedan_marcadores_sin_completar():
    for nombre in ("SALUDO", "HORARIOS", "PRECIOS", "UBICACION_TEXTO", "AYUDA"):
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
    assert datos == ["horarios", "precios", "ubicacion"]


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
