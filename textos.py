"""Todos los textos y datos del negocio, en un solo lugar.

Para adaptar el bot a otro cliente alcanza con cambiar este archivo:
nombre, horarios, precios, servicios, dirección y coordenadas.
"""

NEGOCIO = "Peluquería Aurora"

SALUDO = (
    f"¡Hola! Soy el asistente virtual de {NEGOCIO} 💈\n\n"
    "Puedo responderte las consultas de siempre. ¿Qué necesitás?"
)

# Horarios de atención: (apertura, cierre), con el cierre exclusivo.
# Se usan tanto en el texto de /horarios como en validaciones.py.
HORARIO_SEMANA = (9, 19)
HORARIO_SABADO = (9, 14)

HORARIOS = (
    "🕒 Horarios de atención\n\n"
    f"Lunes a viernes: {HORARIO_SEMANA[0]}:00 a {HORARIO_SEMANA[1]}:00\n"
    f"Sábados: {HORARIO_SABADO[0]}:00 a {HORARIO_SABADO[1]}:00\n"
    "Domingos y feriados: cerrado"
)

PRECIOS = (
    "💲 Precios\n\n"
    "Corte: $8.000\n"
    "Corte + barba: $12.000\n"
    "Color: $20.000\n"
    "Peinado: $6.000\n\n"
    "El precio final puede variar según el largo del cabello."
)

# Datos del local. Las coordenadas se sacan de Google Maps:
# clic derecho sobre el local → "¿Qué hay aquí?" → copiar los dos números.
DIRECCION = "Av. Siempreviva 742, CABA"
LATITUD = -34.6037
LONGITUD = -58.3816

UBICACION_TEXTO = (
    "📍 Dónde estamos\n\n"
    f"{DIRECCION}\n"
    "A dos cuadras del subte.\n\n"
    "Te mando el mapa acá abajo 👇"
)

# Respuestas de los botones del menú (la clave es el callback_data).
CONSULTAS = {
    "horarios": HORARIOS,
    "precios": PRECIOS,
}

# --- Reserva de turnos ----------------------------------------------------

# Opciones que aparecen como botones al reservar.
SERVICIOS = ["Corte", "Corte + barba", "Color", "Peinado"]

RESERVA_INTRO = "📅 Perfecto, vamos a reservar tu turno."

PREGUNTA_NOMBRE = "¿Cómo te llamás?"

PREGUNTA_SERVICIO = "¿Qué servicio querés?"

PREGUNTA_HORA = (
    "¿Qué día y hora te queda cómodo?\n\n"
    "Escribilo así: 25/11 15:00\n"
    "También podés incluir el año: 25/11/2026 15:00\n\n"
    "Podés cancelar cuando quieras con /cancelar."
)

# Errores de validación (los usa validaciones.py).
ERROR_FECHA_FORMATO = (
    "No entendí la fecha. Escribila así: 25/11 15:00 "
    "o 25/11/2026 15:00."
)
ERROR_FECHA_PASADA = "Esa fecha ya pasó. Elegí una futura."
ERROR_DOMINGO = "Los domingos no atendemos. Elegí de lunes a sábado."
ERROR_FUERA_DE_HORARIO = (
    "Fuera del horario de atención: lunes a viernes de 9:00 a 19:00 "
    "y sábados de 9:00 a 14:00."
)

TURNO_OCUPADO = (
    "😕 Ese horario ya está ocupado.\n\n"
    "🕒 Ya reservados el {dia}: {horas}\n\n"
    "Elegí otro horario (o mandá /cancelar)."
)

CONFIRMACION = (
    "✅ Turno reservado\n\n"
    "👤 {nombre}\n"
    "✂️ {servicio}\n"
    "🕒 {cuando}\n\n"
    "Te esperamos. Si necesitás cambiarlo, mandá /reservar de nuevo."
)

RESERVA_CANCELADA = (
    "Reserva cancelada. Cuando quieras, empezá de nuevo con /reservar."
)

SIN_RESERVA = "No hay ninguna reserva en curso. Para sacar un turno mandá /reservar."

RESERVA_INTERRUMPIDA = "Cancelé la reserva que tenías a medias."

AYUDA = (
    "Esto es lo que puedo hacer por ahora:\n\n"
    "/start — menú principal con botones\n"
    "/reservar — sacar un turno paso a paso\n"
    "/cancelar — cancelar una reserva a medias\n"
    "/horarios — días y horas de atención\n"
    "/precios — lista de precios\n"
    "/ubicacion — dirección y mapa\n"
    "/ayuda — este mensaje\n\n"
    "¿Querés un turno? Mandá /reservar."
)

OPCION_INVALIDA = "Esa opción ya no está disponible. Te dejo el menú de nuevo 👇"

MENSAJE_ERROR = "Uy, algo salió mal de mi lado. Probá de nuevo en un ratito."
