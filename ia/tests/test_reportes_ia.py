import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reportes_ia import validar_rango


def test_validar_rango_acepta_periodo_valido():
    inicio, fin = validar_rango("2025-01-01", "2025-12-31")
    assert str(inicio) == "2025-01-01"
    assert str(fin) == "2025-12-31"


def test_validar_rango_rechaza_fechas_invertidas():
    with pytest.raises(ValueError, match="inicial"):
        validar_rango("2025-12-31", "2025-01-01")
