"""Lógica conversacional de Finbot: reglas primero, OpenAI solo para preguntas abiertas."""

import json
import os
import re
import unicodedata
import urllib.error
import urllib.request

from app import finanzas

AVISO = "Esto es educativo, no una recomendación financiera."

GLOSARIO = {
    "uf": (
        "La UF (Unidad de Fomento) es una unidad de cuenta que se reajusta a diario según "
        "la inflación (IPC). La publica el Banco Central y se usa en créditos hipotecarios, "
        "arriendos y seguros para mantener el valor real de los montos."
    ),
    "cae": (
        "En Chile, CAE tiene dos sentidos: (1) Crédito con Aval del Estado, que financia "
        "estudios de educación superior con garantía estatal; y (2) Carga Anual Equivalente, "
        "un indicador obligatorio en los créditos que resume en un porcentaje anual su costo "
        "total (intereses, comisiones y seguros). Sirve para comparar créditos: menor CAE, "
        "crédito más barato."
    ),
    "apv": (
        "El APV (Ahorro Previsional Voluntario) es ahorro extra para la pensión, además de la "
        "cotización obligatoria. Tiene beneficios tributarios en dos regímenes: el A, con una "
        "bonificación fiscal del 15% de lo ahorrado (con tope anual), y el B, que rebaja lo "
        "ahorrado de la base imponible del impuesto a la renta."
    ),
    "inflacion": (
        "La inflación es el alza sostenida y generalizada de los precios. En Chile se mide con "
        "el IPC que publica el INE. El Banco Central busca mantenerla cerca de 3% anual. Con "
        "inflación, el mismo dinero compra menos con el tiempo."
    ),
    "fondo mutuo": (
        "Un fondo mutuo junta el dinero de muchas personas (partícipes) y lo invierte en "
        "instrumentos como acciones o bonos. Lo administra una AGF fiscalizada por la CMF. "
        "Compras cuotas cuyo valor sube o baja: la rentabilidad no está garantizada."
    ),
}

AYUDA = (
    "Puedo ayudarte con:\n"
    "• Cuota de un crédito: «cuota de un crédito de 5.000.000 a 24 meses al 1,5% mensual»\n"
    "• Ahorro para una meta: «quiero ahorrar 2 millones en 12 meses»\n"
    "• Interés compuesto: «si invierto 1.000.000 al 6% anual por 5 años»\n"
    "• Conceptos: UF, CAE, APV, inflación, fondo mutuo."
)

INTENCIONES = {
    "credito": ("cuota", "credito", "prestamo", "dividendo"),
    "ahorro": ("ahorrar", "ahorro", "meta", "juntar"),
    "compuesto": ("interes compuesto", "invierto", "invertir", "inversion", "rentabilidad"),
}


class FaltanDatos(Exception):
    """El mensaje tiene una intención clara pero le faltan números para calcular."""


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def _a_numero(texto: str) -> float:
    """Interpreta números en formato chileno: 5.000.000 / 1,5 / 1.5."""
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        return float(texto.replace(".", ""))
    return float(texto.replace(".", "").replace(",", ".") if "," in texto else texto)


def _pesos(valor: float) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _extraer_tasa(texto: str) -> tuple[float, str] | None:
    """Devuelve (tasa como fracción, 'mensual'|'anual'). Sin indicación se asume anual."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%(.{0,20})", texto)
    if not m:
        return None
    periodo = "mensual" if "mensual" in m.group(2) or "al mes" in m.group(2) else "anual"
    return _a_numero(m.group(1)) / 100, periodo


def _extraer_meses(texto: str) -> int | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(meses|mes|anos|ano)\b", texto)
    if not m:
        return None
    valor = _a_numero(m.group(1))
    return round(valor * 12 if m.group(2).startswith("ano") else valor)


def _extraer_monto(texto: str) -> float | None:
    """Primer monto que no sea tasa ni plazo. Acepta 'millones', 'mil' y 'mm'."""
    patron = r"(\d+(?:[.,]\d+)*)\s*(millones|millon|mm|mil\b)?"
    for m in re.finditer(patron, texto):
        if re.match(r"\s*(%|meses\b|mes\b|anos?\b)", texto[m.end():]):
            continue
        valor = _a_numero(m.group(1))
        sufijo = m.group(2)
        if sufijo in ("millones", "millon", "mm"):
            valor *= 1_000_000
        elif sufijo == "mil":
            valor *= 1_000
        if valor > 0:
            return valor
    return None


def _detectar_intencion(texto: str) -> str | None:
    for intencion, palabras in INTENCIONES.items():
        if any(p in texto for p in palabras):
            return intencion
    return None


def _buscar_glosario(texto: str) -> str | None:
    for termino, definicion in GLOSARIO.items():
        if re.search(rf"\b{termino}s?\b", texto):
            return definicion
    return None


def _calcular(intencion: str, texto: str) -> str:
    monto = _extraer_monto(texto)
    meses = _extraer_meses(texto)
    tasa = _extraer_tasa(texto)

    if intencion == "credito":
        if not (monto and meses and tasa):
            raise FaltanDatos("Para calcular la cuota necesito monto, plazo y tasa. Ej.: «cuota de un "
                    "crédito de 5.000.000 a 24 meses al 1,5% mensual».")
        i = tasa[0] if tasa[1] == "mensual" else finanzas.tasa_anual_a_mensual(tasa[0])
        cuota = finanzas.cuota_mensual(monto, i, meses)
        total, intereses = finanzas.total_pagado_e_intereses(monto, i, meses)
        return (f"Con un crédito de {_pesos(monto)} a {meses} meses y una tasa de "
                f"{i * 100:.2f}% mensual (sistema francés):\n"
                f"• Cuota mensual: {_pesos(cuota)}\n"
                f"• Total pagado: {_pesos(total)}\n"
                f"• Intereses: {_pesos(intereses)}\n"
                "Ojo: no incluye seguros ni comisiones; compara créditos usando la CAE.")

    if intencion == "ahorro":
        if not (monto and meses):
            raise FaltanDatos("Para tu meta necesito el monto y el plazo. Ej.: «quiero ahorrar 2 "
                    "millones en 12 meses» (opcional: «al 0,4% mensual»).")
        i = 0.0
        if tasa:
            i = tasa[0] if tasa[1] == "mensual" else finanzas.tasa_anual_a_mensual(tasa[0])
        deposito = finanzas.ahorro_mensual_para_meta(monto, meses, i)
        detalle = f" con una rentabilidad de {i * 100:.2f}% mensual" if i else " sin rentabilidad"
        return (f"Para juntar {_pesos(monto)} en {meses} meses{detalle}, necesitas ahorrar "
                f"{_pesos(deposito)} al mes.")

    # interés compuesto
    if not (monto and meses and tasa):
        raise FaltanDatos("Para el interés compuesto necesito capital, tasa anual y plazo. Ej.: «si "
                "invierto 1.000.000 al 6% anual por 5 años».")
    tasa_anual = tasa[0] if tasa[1] == "anual" else tasa[0] * 12
    anios = meses / 12
    final = finanzas.interes_compuesto(monto, tasa_anual, anios)
    return (f"Si inviertes {_pesos(monto)} al {tasa_anual * 100:.2f}% anual "
            f"(capitalización mensual) durante {anios:g} años, tendrías {_pesos(final)}: "
            f"{_pesos(final - monto)} de intereses. La rentabilidad pasada no garantiza la futura.")


def _preguntar_openai(mensaje: str) -> str | None:
    """Consulta a OpenAI con la API HTTP (sin SDK). Devuelve None si falla."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    cuerpo = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": (
                "Eres Finbot, un asistente de educación financiera para Chile. Responde en "
                "español, breve y claro, con conceptos y contexto chileno (UF, AFP, CMF, SII). "
                "No des recomendaciones de inversión personalizadas ni inventes cifras vigentes; "
                "si algo depende de datos actuales, sugiere consultar fuentes oficiales.")},
            {"role": "user", "content": mensaje},
        ],
        "temperature": 0.3,
    }
    solicitud = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(cuerpo).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=20) as r:
            datos = json.load(r)
        return datos["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError):
        return None


def responder(mensaje: str) -> dict:
    """Devuelve {"respuesta": str, "fuente": "reglas"|"glosario"|"llm"|"ayuda"}."""
    texto = _normalizar(mensaje)

    # Sin ningún número no hay nada que calcular: se trata como pregunta abierta.
    intencion = _detectar_intencion(texto) if re.search(r"\d", texto) else None
    definicion = _buscar_glosario(texto)

    # Una pregunta tipo "¿qué es el APV?" va al glosario aunque contenga "ahorro".
    if definicion and (not intencion or re.search(r"\bque (es|son|significa)\b", texto)):
        return {"respuesta": definicion, "fuente": "glosario"}

    if intencion:
        try:
            return {"respuesta": f"{_calcular(intencion, texto)}\n{AVISO}", "fuente": "reglas"}
        except FaltanDatos as e:
            return {"respuesta": str(e), "fuente": "reglas"}
        except ValueError as e:
            return {"respuesta": f"No pude calcularlo: {e}", "fuente": "reglas"}

    respuesta_ia = _preguntar_openai(mensaje)
    if respuesta_ia:
        return {"respuesta": respuesta_ia, "fuente": "llm"}

    return {"respuesta": AYUDA, "fuente": "ayuda"}
