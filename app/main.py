"""API de Finbot."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


def _cargar_env(ruta: Path = Path(__file__).resolve().parent.parent / ".env") -> None:
    """Carga un .env simple (CLAVE=valor) sin depender de python-dotenv."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env()

from app.bot import responder  # noqa: E402  (después de cargar .env)

app = FastAPI(title="Finbot", description="Asistente de educación financiera para Chile")


class ChatEntrada(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=2000)


class ChatSalida(BaseModel):
    respuesta: str
    fuente: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Endpoint síncrono: FastAPI lo ejecuta en un hilo, así la llamada a OpenAI no bloquea el servidor.
@app.post("/chat", response_model=ChatSalida)
def chat(entrada: ChatEntrada) -> dict:
    return responder(entrada.mensaje)


PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finbot</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 0 auto; padding: 16px; }
  #log { border: 1px solid #ccc; border-radius: 8px; height: 60vh; overflow-y: auto; padding: 8px; }
  .msg { margin: 6px 0; padding: 8px 10px; border-radius: 8px; white-space: pre-wrap; }
  .yo { background: #e3f2fd; text-align: right; }
  .bot { background: #f1f1f1; }
  .fuente { font-size: 0.75em; color: #666; }
  form { display: flex; gap: 8px; margin-top: 8px; }
  input { flex: 1; padding: 8px; }
</style>
</head>
<body>
<h1>Finbot 🇨🇱</h1>
<div id="log"></div>
<form id="f">
  <input id="m" placeholder="Ej.: ¿Qué es la UF?" autocomplete="off" required>
  <button>Enviar</button>
</form>
<script>
const log = document.getElementById("log");
function agregar(texto, clase, fuente) {
  const d = document.createElement("div");
  d.className = "msg " + clase;
  d.textContent = texto;
  if (fuente) {
    const s = document.createElement("div");
    s.className = "fuente";
    s.textContent = "fuente: " + fuente;
    d.appendChild(s);
  }
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}
document.getElementById("f").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("m");
  const mensaje = input.value.trim();
  if (!mensaje) return;
  agregar(mensaje, "yo");
  input.value = "";
  try {
    const r = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({mensaje}),
    });
    const datos = await r.json();
    agregar(datos.respuesta, "bot", datos.fuente);
  } catch {
    agregar("Error de conexión.", "bot");
  }
});
agregar("Hola, soy Finbot. Pregúntame por una cuota, una meta de ahorro, interés compuesto o conceptos como UF o APV.", "bot");
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def inicio() -> str:
    return PAGINA
