import pytest

from app import finanzas


def test_tasa_anual_a_mensual_es_nominal():
    assert finanzas.tasa_anual_a_mensual(0.12) == pytest.approx(0.01)


def test_cuota_10_millones_36_meses_12_anual():
    i = finanzas.tasa_anual_a_mensual(0.12)
    assert round(finanzas.cuota_mensual(10_000_000, i, 36)) == 332_143


def test_total_pagado_e_intereses():
    i = finanzas.tasa_anual_a_mensual(0.12)
    total, intereses = finanzas.total_pagado_e_intereses(10_000_000, i, 36)
    cuota = finanzas.cuota_mensual(10_000_000, i, 36)
    assert total == pytest.approx(cuota * 36)
    assert intereses == pytest.approx(total - 10_000_000)
    assert round(intereses) == 1_957_152


def test_cuota_con_tasa_cero_divide_el_monto():
    assert finanzas.cuota_mensual(1_200_000, 0, 12) == pytest.approx(100_000)


def test_ahorro_para_meta_sin_rentabilidad():
    assert finanzas.ahorro_mensual_para_meta(2_000_000, 12) == pytest.approx(2_000_000 / 12)


def test_ahorro_para_meta_con_rentabilidad_alcanza_la_meta():
    i, n, meta = 0.005, 24, 3_000_000
    deposito = finanzas.ahorro_mensual_para_meta(meta, n, i)
    # Valor futuro de los depósitos a fin de mes.
    valor_futuro = sum(deposito * (1 + i) ** (n - k) for k in range(1, n + 1))
    assert valor_futuro == pytest.approx(meta)
    assert deposito < meta / n


def test_interes_compuesto_capitalizacion_mensual():
    assert round(finanzas.interes_compuesto(1_000_000, 0.06, 5)) == 1_348_850


def test_interes_compuesto_capitalizacion_anual():
    assert finanzas.interes_compuesto(1_000, 0.10, 2, 1) == pytest.approx(1_210)


@pytest.mark.parametrize("llamada", [
    lambda: finanzas.cuota_mensual(0, 0.01, 12),
    lambda: finanzas.cuota_mensual(1_000, 0.01, 0),
    lambda: finanzas.cuota_mensual(1_000, -0.01, 12),
    lambda: finanzas.ahorro_mensual_para_meta(1_000, 0),
    lambda: finanzas.interes_compuesto(1_000, 0.05, 0),
])
def test_datos_invalidos_lanzan_value_error(llamada):
    with pytest.raises(ValueError):
        llamada()
