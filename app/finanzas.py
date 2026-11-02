"""Funciones financieras puras (sin efectos secundarios).

Las tasas se expresan como fracción: 1,5% mensual -> 0.015.
"""


def tasa_anual_a_mensual(tasa_anual: float) -> float:
    """Tasa nominal: anual / 12 (convención de los créditos de consumo en Chile)."""
    return tasa_anual / 12


def cuota_mensual(monto: float, tasa_mensual: float, meses: int) -> float:
    """Cuota fija del sistema francés: C = P * i / (1 - (1 + i)^-n)."""
    if monto <= 0 or meses <= 0:
        raise ValueError("El monto y el plazo deben ser mayores que cero.")
    if tasa_mensual < 0:
        raise ValueError("La tasa no puede ser negativa.")
    if tasa_mensual == 0:
        return monto / meses
    return monto * tasa_mensual / (1 - (1 + tasa_mensual) ** -meses)


def total_pagado_e_intereses(monto: float, tasa_mensual: float, meses: int) -> tuple[float, float]:
    """Devuelve (total pagado, intereses pagados) de un crédito con sistema francés."""
    total = cuota_mensual(monto, tasa_mensual, meses) * meses
    return total, total - monto


def ahorro_mensual_para_meta(meta: float, meses: int, tasa_mensual: float = 0.0) -> float:
    """Depósito mensual (a fin de mes) necesario para juntar `meta` en `meses`."""
    if meta <= 0 or meses <= 0:
        raise ValueError("La meta y el plazo deben ser mayores que cero.")
    if tasa_mensual < 0:
        raise ValueError("La tasa no puede ser negativa.")
    if tasa_mensual == 0:
        return meta / meses
    return meta * tasa_mensual / ((1 + tasa_mensual) ** meses - 1)


def interes_compuesto(capital: float, tasa_anual: float, anios: float,
                      capitalizaciones_por_anio: int = 12) -> float:
    """Valor final: VF = C * (1 + r/m)^(m*t)."""
    if capital <= 0 or anios <= 0 or capitalizaciones_por_anio <= 0:
        raise ValueError("El capital, el plazo y la capitalización deben ser mayores que cero.")
    m = capitalizaciones_por_anio
    return capital * (1 + tasa_anual / m) ** (m * anios)
