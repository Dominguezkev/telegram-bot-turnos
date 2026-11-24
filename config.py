"""Configuración del bot, leída del archivo .env.

El token y el ID del dueño NUNCA van en el código ni en GitHub: viven en
.env, que está ignorado por git. Si el archivo no existe, copiá .env.example
y completalo.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Carga el .env de la carpeta del proyecto, sin importar desde dónde se ejecute.
load_dotenv(BASE_DIR / ".env")


def obtener_token() -> str:
    """Devuelve el token de BotFather o corta con un mensaje claro."""
    token = os.getenv("TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Falta el token del bot.\n\n"
            "1. Copiá .env.example como .env\n"
            "2. Completá TOKEN con el que te dio @BotFather\n"
        )
    return token


def obtener_owner_id() -> int | None:
    """Devuelve el ID del dueño o None si todavía no lo configuró.

    Es opcional: sin OWNER_ID el bot atiende igual, solo que no manda avisos.
    """
    valor = os.getenv("OWNER_ID", "").strip()
    if not valor:
        return None
    if not valor.isdigit():
        raise SystemExit(
            "OWNER_ID tiene que ser un número (el que te da @userinfobot)."
        )
    return int(valor)
