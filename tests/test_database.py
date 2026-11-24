# tests/test_database.py
"""Tests de SQLite con una base temporal (nunca tocan turnos.db real).

Requieren pytest por los fixtures tmp_path y monkeypatch:

    pytest tests/test_database.py
"""
import sqlite3
from contextlib import closing
from datetime import date, datetime

import database


def preparar(tmp_path, monkeypatch):
    """Apunta database.DB a un archivo temporal y crea la tabla."""
    monkeypatch.setattr(database, "DB", str(tmp_path / "test.db"))
    database.init_db()


def test_no_permite_duplicados(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    fecha = datetime(2026, 11, 25, 15, 0)

    assert database.guardar_turno(1, "Ana", "Corte", fecha) is True
    assert database.guardar_turno(2, "Beto", "Color", fecha) is False


def test_otro_horario_del_mismo_dia_se_guarda(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)

    assert database.guardar_turno(
        1, "Ana", "Corte", datetime(2026, 11, 25, 15, 0)
    ) is True
    assert database.guardar_turno(
        2, "Beto", "Color", datetime(2026, 11, 25, 16, 0)
    ) is True


def test_init_db_se_puede_llamar_varias_veces(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    database.init_db()
    database.init_db()

    assert database.guardar_turno(
        1, "Ana", "Corte", datetime(2026, 11, 25, 15, 0)
    ) is True


def test_horarios_ocupados_del_dia(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    database.guardar_turno(1, "Ana", "Corte", datetime(2026, 11, 25, 17, 30))
    database.guardar_turno(2, "Beto", "Color", datetime(2026, 11, 25, 15, 0))
    database.guardar_turno(3, "Caro", "Peinado", datetime(2026, 11, 26, 10, 0))

    assert database.horarios_ocupados(date(2026, 11, 25)) == ["15:00", "17:30"]


def test_horarios_ocupados_dia_sin_turnos(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)

    assert database.horarios_ocupados(date(2026, 11, 25)) == []


def test_nombre_con_sql_no_rompe_la_base(tmp_path, monkeypatch):
    # Si el INSERT se armara pegando texto, esto borraría la tabla.
    preparar(tmp_path, monkeypatch)
    peligroso = "Ana'); DROP TABLE turnos;--"

    assert database.guardar_turno(
        1, peligroso, "Corte", datetime(2026, 11, 25, 15, 0)
    ) is True

    with closing(sqlite3.connect(database.DB)) as con:
        fila = con.execute("SELECT nombre FROM turnos").fetchone()
        cantidad_tablas = con.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'turnos'"
        ).fetchone()[0]

    assert fila[0] == peligroso, "el nombre tiene que guardarse tal cual"
    assert cantidad_tablas == 1, "la tabla sigue existiendo"
