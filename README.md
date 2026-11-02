# Finbot

Asistente de educación financiera para Chile, hecho con FastAPI.

- Calcula la **cuota de un crédito** (sistema francés), el total pagado y los intereses.
- Calcula cuánto **ahorrar al mes** para llegar a una meta.
- Simula **interés compuesto**.
- Explica conceptos: **UF, CAE, APV, inflación y fondo mutuo**.
- Responde preguntas abiertas con OpenAI, solo si configuras `OPENAI_API_KEY`.

> Finbot es educativo y no entrega recomendaciones financieras.

**Pruébalo en línea:** https://finbot-529588732198.southamerica-west1.run.app
(desplegado en Google Cloud Run, región Santiago).

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env          # opcional: agrega tu OPENAI_API_KEY
uvicorn app.main:app --reload
```

Abre http://127.0.0.1:8000 para usar el chat, o http://127.0.0.1:8000/docs para ver la API.

## API

| Método | Ruta      | Descripción                                        |
|--------|-----------|----------------------------------------------------|
| GET    | `/`       | Chat HTML mínimo                                   |
| GET    | `/health` | Estado del servicio                                |
| POST   | `/chat`   | `{"mensaje": "..."}` → `{"respuesta", "fuente"}`   |

`fuente` puede ser:

- `reglas`: cálculo hecho por reglas, o aviso de que faltan datos.
- `glosario`: definición de un concepto.
- `llm`: respuesta de OpenAI a una pregunta abierta.
- `ayuda`: mensaje de ayuda cuando no se entendió la pregunta.

## Ejemplos de mensajes

- «cuota de un crédito de 5.000.000 a 24 meses al 1,5% mensual»
- «quiero ahorrar 2 millones en 12 meses»
- «si invierto 1.000.000 al 6% anual por 5 años»
- «¿qué es el APV?»

Si no indicas si la tasa es mensual o anual, Finbot la considera **anual**. Las tasas
anuales se pasan a mensuales como tasa nominal (anual / 12), la convención de los créditos
de consumo en Chile.

## Desarrollo

Para las pruebas, instala también las dependencias de desarrollo (`pytest` y `httpx`):

```bash
pip install -r requirements-dev.txt
pytest
```
