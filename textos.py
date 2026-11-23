"""Todos los textos y datos del negocio, en un solo lugar.

Para adaptar el bot a otro cliente alcanza con cambiar este archivo:
nombre, horarios, precios, dirección y coordenadas.
"""

NEGOCIO = "Peluquería Aurora"

SALUDO = (
    f"¡Hola! Soy el asistente virtual de {NEGOCIO} 💈\n\n"
    "Puedo responderte las consultas de siempre. ¿Qué necesitás?"
)

HORARIOS = (
    "🕒 Horarios de atención\n\n"
    "Lunes a viernes: 9:00 a 19:00\n"
    "Sábados: 9:00 a 14:00\n"
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

AYUDA = (
    "Esto es lo que puedo hacer por ahora:\n\n"
    "/start — menú principal con botones\n"
    "/horarios — días y horas de atención\n"
    "/precios — lista de precios\n"
    "/ubicacion — dirección y mapa\n"
    "/ayuda — este mensaje\n\n"
    "Pronto también vas a poder reservar tu turno desde acá."
)

OPCION_INVALIDA = "Esa opción ya no está disponible. Te dejo el menú de nuevo 👇"

MENSAJE_ERROR = "Uy, algo salió mal de mi lado. Probá de nuevo en un ratito."
