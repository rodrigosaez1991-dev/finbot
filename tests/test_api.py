import pytest
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


@pytest.fixture(autouse=True)
def sin_openai(monkeypatch):
    """Las pruebas nunca llaman a OpenAI, aunque exista un .env con clave."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def chat(mensaje):
    r = cliente.post("/chat", json={"mensaje": mensaje})
    assert r.status_code == 200
    return r.json()


def test_health():
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cuota_de_credito():
    datos = chat("cuota de un crédito de 10 millones a 36 meses al 12% anual")
    assert datos["fuente"] == "reglas"
    assert "$332.143" in datos["respuesta"]


def test_meta_de_ahorro():
    datos = chat("quiero ahorrar 2 millones en 12 meses")
    assert datos["fuente"] == "reglas"
    assert "$166.667" in datos["respuesta"]


def test_termino_del_glosario():
    datos = chat("¿Qué es la UF?")
    assert datos["fuente"] == "glosario"
    assert "Unidad de Fomento" in datos["respuesta"]


def test_pregunta_abierta_sin_numeros_va_a_ayuda_sin_clave():
    datos = chat("¿me conviene prepagar mi crédito?")
    assert datos["fuente"] == "ayuda"


@pytest.mark.parametrize("cuerpo", [{"mensaje": ""}, {}])
def test_entrada_vacia_es_rechazada(cuerpo):
    r = cliente.post("/chat", json=cuerpo)
    assert r.status_code == 422
