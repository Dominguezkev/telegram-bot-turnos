# tests/test_validaciones.py
"""Tests de validar_fecha con un "ahora" fijo (nunca datetime.now()).

Así los tests no cambian según el día en que se corran.

Con pytest:
    pytest tests/test_validaciones.py

Sin pytest:
    python tests/test_validaciones.py
"""
import sys
from datetime import datetime
from pathlib import Path

# Permite importar validaciones.py y textos.py desde cualquier carpeta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import textos              # noqa: E402
from validaciones import validar_fecha, validar_nombre   # noqa: E402

# Martes 24/11/2026 a las 10:00. Todos los tests parten de esta fecha.
AHORA = datetime(2026, 11, 24, 10, 0)


def test_fecha_valida():
    fecha, error = validar_fecha("25/11 15:00", AHORA)

    assert error is None
    assert fecha == datetime(2026, 11, 25, 15, 0)


def test_formato_invalido():
    for texto in ("mañana", "25-11 15:00", "31/02 15:00", ""):
        fecha, error = validar_fecha(texto, AHORA)
        assert fecha is None
        assert error == textos.ERROR_FECHA_FORMATO, f"falló con {texto!r}"


def test_fecha_pasada():
    _, error = validar_fecha("20/11 15:00", AHORA)
    assert error == textos.ERROR_FECHA_PASADA


def test_hoy_mas_temprano_es_pasado():
    # Son las 10:00: un turno para hoy a las 9:00 ya pasó.
    _, error = validar_fecha("24/11 09:00", AHORA)
    assert error == textos.ERROR_FECHA_PASADA


def test_domingo():
    assert datetime(2026, 11, 29).weekday() == 6  # el test depende de esto
    _, error = validar_fecha("29/11 15:00", AHORA)
    assert error == textos.ERROR_DOMINGO


def test_fuera_de_horario():
    for texto in ("25/11 21:00", "25/11 08:59"):
        _, error = validar_fecha(texto, AHORA)
        assert error == textos.ERROR_FUERA_DE_HORARIO, f"falló con {texto!r}"


def test_apertura_y_cierre():
    # 9:00 abre; 19:00 ya está cerrado.
    fecha, error = validar_fecha("25/11 09:00", AHORA)
    assert error is None and fecha.hour == 9

    _, error = validar_fecha("25/11 19:00", AHORA)
    assert error == textos.ERROR_FUERA_DE_HORARIO


def test_sabado_tiene_horario_mas_corto():
    # Sábado 28/11: se atiende de 9:00 a 14:00.
    fecha, error = validar_fecha("28/11 13:00", AHORA)
    assert error is None and fecha.weekday() == 5

    _, error = validar_fecha("28/11 14:00", AHORA)
    assert error == textos.ERROR_FUERA_DE_HORARIO


def test_formato_con_anio():
    fecha, error = validar_fecha("25/11/2027 15:00", AHORA)

    assert error is None
    assert fecha == datetime(2027, 11, 25, 15, 0)


def test_anio_explicito_del_anio_actual():
    fecha, error = validar_fecha("25/11/2026 15:00", AHORA)
    assert error is None and fecha.year == 2026


def test_anio_explicito_pasado():
    _, error = validar_fecha("25/11/2025 15:00", AHORA)
    assert error == textos.ERROR_FECHA_PASADA


def test_espacios_alrededor_no_molestan():
    fecha, error = validar_fecha("  25/11 15:00  ", AHORA)
    assert error is None and fecha.hour == 15


def test_fin_de_anio_pasa_al_anio_siguiente():
    # En diciembre, "05/01" se entiende como enero del año que viene.
    ahora_diciembre = datetime(2026, 12, 20, 10, 0)

    fecha, error = validar_fecha("05/01 15:00", ahora_diciembre)

    assert error is None
    assert fecha == datetime(2027, 1, 5, 15, 0)


def test_enero_en_noviembre_sigue_siendo_pasado():
    # En noviembre, "05/01" es enero de este año: ya pasó.
    _, error = validar_fecha("05/01 15:00", AHORA)
    assert error == textos.ERROR_FECHA_PASADA


def test_nombre_valido_y_limpio():
    nombre, error = validar_nombre("  Ana   María ")

    assert error is None
    assert nombre == "Ana María"


def test_nombre_muy_corto_o_largo():
    assert validar_nombre("A")[1] == textos.ERROR_NOMBRE
    assert validar_nombre("x" * 51)[1] == textos.ERROR_NOMBRE


def test_nombre_en_los_limites():
    assert validar_nombre("Al")[0] == "Al"
    assert validar_nombre("x" * 50)[0] == "x" * 50


def test_nombre_solo_espacios():
    assert validar_nombre("   \n\t ")[1] == textos.ERROR_NOMBRE


def test_nombre_con_tabs_y_saltos_se_normaliza():
    assert validar_nombre("Ana\tMaría\nPérez")[0] == "Ana María Pérez"


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
