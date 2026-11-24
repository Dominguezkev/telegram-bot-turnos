# tests/test_config.py
"""Tests de la lectura de OWNER_ID desde el entorno.

Requieren pytest por monkeypatch y pytest.raises:

    pytest tests/test_config.py
"""
import pytest

from config import obtener_owner_id


def test_owner_id_no_configurado(monkeypatch):
    monkeypatch.delenv("OWNER_ID", raising=False)

    assert obtener_owner_id() is None


def test_owner_id_valido(monkeypatch):
    monkeypatch.setenv("OWNER_ID", "123456789")

    assert obtener_owner_id() == 123456789


def test_owner_id_invalido_corta_con_mensaje(monkeypatch):
    monkeypatch.setenv("OWNER_ID", "no-es-un-numero")

    with pytest.raises(SystemExit):
        obtener_owner_id()
