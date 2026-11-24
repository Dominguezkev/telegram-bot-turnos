"""Acceso a SQLite: tabla de turnos y operaciones.

El archivo ``turnos.db`` vive junto al bot y está ignorado por git porque
contiene datos de clientes. En el despliegue (Railway/Render) va a necesitar
un volumen persistente o PostgreSQL.
"""
import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

DB = str(Path(__file__).resolve().parent / "turnos.db")


def _conectar() -> sqlite3.Connection:
    return sqlite3.connect(DB)


def init_db() -> None:
    """Crea la tabla si no existe. Se puede llamar en cada arranque."""
    with closing(_conectar()) as con, con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                servicio TEXT NOT NULL,
                fecha_hora TEXT NOT NULL UNIQUE
            )
            """
        )


def guardar_turno(
    chat_id: int, nombre: str, servicio: str, fecha: datetime
) -> bool:
    """Guarda un turno. Devuelve False si ese horario ya estaba ocupado.

    Los valores van con ``?`` (consultas parametrizadas): así un nombre con
    comillas o SQL adentro se guarda como texto y no altera la base.
    """
    try:
        with closing(_conectar()) as con, con:
            con.execute(
                "INSERT INTO turnos (chat_id, nombre, servicio, fecha_hora) "
                "VALUES (?, ?, ?, ?)",
                (chat_id, nombre, servicio, fecha.strftime("%Y-%m-%d %H:%M")),
            )
        return True
    except sqlite3.IntegrityError:
        # La restricción UNIQUE de fecha_hora impide dos turnos a la misma hora.
        return False


def horarios_ocupados(dia: date | datetime) -> list[str]:
    """Devuelve las horas ya reservadas para ese día, ej: ['15:00', '17:30']."""
    patron = f"{dia.strftime('%Y-%m-%d')}%"
    with closing(_conectar()) as con:
        filas = con.execute(
            "SELECT fecha_hora FROM turnos WHERE fecha_hora LIKE ? "
            "ORDER BY fecha_hora",
            (patron,),
        ).fetchall()
    return [fila[0][11:16] for fila in filas]
