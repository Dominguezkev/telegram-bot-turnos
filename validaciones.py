"""Validación de fechas y horarios de atención, sin nada de Telegram.

Separar esta lógica de los handlers permite testearla con fechas fijas y
reutilizarla si algún día el negocio suma WhatsApp o una web.
"""
from datetime import datetime

import textos

# Horarios de atención: (apertura, cierre), con el cierre exclusivo.
# Lunes a viernes de 9:00 a 19:00; sábados de 9:00 a 14:00; domingos cerrado.
# Los valores viven en textos.py para que el texto y la validación no se
# desincronicen cuando el negocio cambia de horario.
SABADO = 5
DOMINGO = 6

# Se prueban en orden. El formato con año va primero para no confundirlo
# con el formato corto.
FORMATO_CON_ANIO = "%d/%m/%Y %H:%M"


def _parsear(texto: str, anio_base: int) -> tuple[datetime | None, bool]:
    """Prueba los formatos aceptados y dice si el texto traía año.

    Al formato corto le agregamos un año antes de parsear: si se lo dejamos
    afuera, Python 3.14 avisa que la fecha es ambigua (y en 3.15 va a cambiar).
    """
    texto = texto.strip()

    try:
        return datetime.strptime(texto, FORMATO_CON_ANIO), True
    except ValueError:
        pass

    partes = texto.split()
    if len(partes) != 2:
        return None, False

    fecha_texto, hora_texto = partes
    try:
        return datetime.strptime(
            f"{fecha_texto}/{anio_base} {hora_texto}", FORMATO_CON_ANIO
        ), False
    except ValueError:
        return None, False


def validar_fecha(
    texto: str, ahora: datetime | None = None
) -> tuple[datetime | None, str | None]:
    """Devuelve (fecha, None) si es válida, o (None, mensaje) si no.

    Acepta ``25/11 15:00`` y ``25/11/2026 15:00``. Si no trae año, usa el año
    actual. El parámetro ``ahora`` existe para que los tests no dependan del
    reloj real.
    """
    if ahora is None:
        ahora = datetime.now()

    fecha, tiene_anio = _parsear(texto, ahora.year)
    if fecha is None:
        return None, textos.ERROR_FECHA_FORMATO

    if not tiene_anio:
        # Caso fin de año: en diciembre, "05/01" es enero del año siguiente.
        if fecha < ahora and ahora.month == 12 and fecha.month == 1:
            fecha = fecha.replace(year=ahora.year + 1)

    if fecha < ahora:
        return None, textos.ERROR_FECHA_PASADA

    if fecha.weekday() == DOMINGO:
        return None, textos.ERROR_DOMINGO

    apertura, cierre = (
        textos.HORARIO_SABADO
        if fecha.weekday() == SABADO
        else textos.HORARIO_SEMANA
    )
    if not (apertura <= fecha.hour < cierre):
        return None, textos.ERROR_FUERA_DE_HORARIO

    return fecha, None
