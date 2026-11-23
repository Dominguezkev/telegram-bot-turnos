"""Configuración del bot, leída del archivo .env.

El token NUNCA va en el código ni en GitHub: vive en .env, que está
ignorado por git. Si el archivo no existe, copiá .env.example y completalo.
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
