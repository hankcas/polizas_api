"""API web del agente (FastAPI).

Para correrla, desde la carpeta agente/:
    uvicorn app.main:app --reload
y abrir http://localhost:8000/docs para probarla.
"""

import logging
import uuid
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.agente import Agente, UsoHerramienta
from app.agent.llm import ErrorLLM, Mensaje, crear_proveedor
from app.config import get_settings
from app.tools.cliente_api import ClienteApiPolizas
from app.tools.herramientas import crear_herramientas

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Agente de pólizas",
    description="Agente de IA que responde preguntas sobre pólizas de seguro usando la API de pólizas.",
)

# Conversaciones en memoria: sesion_id -> mensajes. Se pierden al reiniciar;
# en producción irían en una base de datos o en Redis.
_sesiones: dict[str, list[Mensaje]] = {}


class PeticionChat(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000, examples=["¿Qué pólizas colectivas están activas?"])
    sesion_id: str | None = Field(default=None, description="Vacío para empezar una conversación nueva.")


class RespuestaChat(BaseModel):
    respuesta: str
    sesion_id: str
    herramientas_usadas: list[UsoHerramienta]


@lru_cache  # se crea un solo agente y se reutiliza en todas las peticiones
def obtener_agente() -> Agente:
    settings = get_settings()
    return Agente(crear_proveedor(settings), crear_herramientas(ClienteApiPolizas(settings)))


@app.post("/chat", response_model=RespuestaChat)
def chat(peticion: PeticionChat, agente: Agente = Depends(obtener_agente)) -> RespuestaChat:
    # `Depends` le pide a FastAPI que nos entregue el agente. En las pruebas
    # lo cambiamos por uno con un LLM falso, sin tocar este código.
    sesion_id = peticion.sesion_id or str(uuid.uuid4())
    historial = _sesiones.get(sesion_id, [])
    try:
        resultado = agente.responder(historial, peticion.mensaje)
    except ErrorLLM as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    _sesiones[sesion_id] = resultado.historial
    return RespuestaChat(
        respuesta=resultado.texto,
        sesion_id=sesion_id,
        herramientas_usadas=resultado.herramientas_usadas,
    )


@app.get("/salud")
def salud() -> dict:
    return {"estado": "ok"}
