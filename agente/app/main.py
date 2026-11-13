"""API web del agente (FastAPI).

Para correrla, desde la carpeta agente/:
    uvicorn app.main:app --reload
y abrir http://localhost:8000/docs para probarla.
"""

import logging
import unicodedata
import uuid
from dataclasses import dataclass, field
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.agente import AccionPendiente, Agente, RespuestaAgente, UsoHerramienta
from app.agent.llm import ErrorLLM, Mensaje, crear_proveedor
from app.config import get_settings
from app.rag.buscador import crear_buscador
from app.tools.cliente_api import ClienteApiPolizas
from app.tools.herramientas import crear_herramientas

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Agente de pólizas",
    description="Agente de IA que responde preguntas sobre pólizas de seguro usando la API de pólizas.",
)


@dataclass
class Sesion:
    historial: list[Mensaje] = field(default_factory=list)
    pendiente: AccionPendiente | None = None


# Conversaciones en memoria: sesion_id -> Sesion. Se pierden al reiniciar;
# en producción irían en una base de datos o en Redis.
_sesiones: dict[str, Sesion] = {}

# Respuestas cortas que cuentan como "sí" o "no" a una acción pendiente.
# Comparación exacta, sin LLM: es barata, predecible y no se puede "malinterpretar".
AFIRMATIVAS = {"si", "si confirmo", "confirmo", "confirmar", "dale", "hazlo", "ok", "de acuerdo"}
NEGATIVAS = {"no", "no gracias", "mejor no", "no confirmo"}


class PeticionChat(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000, examples=["¿Qué pólizas colectivas están activas?"])
    sesion_id: str | None = Field(default=None, description="Vacío para empezar una conversación nueva.")


class PeticionConfirmacion(BaseModel):
    sesion_id: str
    accion_id: str
    confirmar: bool = Field(description="true ejecuta la acción; false la descarta.")


class RespuestaChat(BaseModel):
    respuesta: str
    sesion_id: str
    herramientas_usadas: list[UsoHerramienta]
    accion_pendiente: AccionPendiente | None = None


@lru_cache  # se crea un solo agente y se reutiliza en todas las peticiones
def obtener_agente() -> Agente:
    settings = get_settings()
    buscador = crear_buscador(settings.condiciones_pdf, settings.embeddings_modelo, settings.embeddings_cache)
    return Agente(crear_proveedor(settings), crear_herramientas(ClienteApiPolizas(settings), buscador))


@app.post("/chat", response_model=RespuestaChat)
def chat(peticion: PeticionChat, agente: Agente = Depends(obtener_agente)) -> RespuestaChat:
    # `Depends` le pide a FastAPI que nos entregue el agente. En las pruebas
    # lo cambiamos por uno con un LLM falso, sin tocar este código.
    sesion_id = peticion.sesion_id or str(uuid.uuid4())
    sesion = _sesiones.setdefault(sesion_id, Sesion())

    # Si hay una acción esperando y el usuario escribió "sí" o "no", la resolvemos.
    if sesion.pendiente is not None:
        texto = _normalizar(peticion.mensaje)
        if texto in AFIRMATIVAS or texto in NEGATIVAS:
            return _resolver(sesion_id, sesion, agente, confirmar=texto in AFIRMATIVAS)
        # Cualquier otro mensaje descarta la acción: no queremos que un "sí"
        # dicho mucho después confirme algo que el usuario ya olvidó.
        sesion.pendiente = None

    try:
        resultado = agente.responder(sesion.historial, peticion.mensaje)
    except ErrorLLM as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return _guardar(sesion_id, sesion, resultado)


@app.post("/chat/confirmar", response_model=RespuestaChat)
def confirmar(peticion: PeticionConfirmacion, agente: Agente = Depends(obtener_agente)) -> RespuestaChat:
    """Lo usa el botón Confirmar / Cancelar de la interfaz."""
    sesion = _sesiones.get(peticion.sesion_id)
    if sesion is None or sesion.pendiente is None or sesion.pendiente.id != peticion.accion_id:
        raise HTTPException(status_code=409, detail="Esa acción ya no está pendiente. Vuelve a pedirla.")
    return _resolver(peticion.sesion_id, sesion, agente, confirmar=peticion.confirmar)


@app.get("/salud")
def salud() -> dict:
    return {"estado": "ok"}


def _resolver(sesion_id: str, sesion: Sesion, agente: Agente, confirmar: bool) -> RespuestaChat:
    accion = sesion.pendiente
    sesion.pendiente = None  # se usa una sola vez, pase lo que pase
    if confirmar:
        resultado = agente.ejecutar_confirmada(sesion.historial, accion)
    else:
        texto = "Entendido, no hice ningún cambio."
        historial = [
            *sesion.historial,
            Mensaje(rol="usuario", texto=f"No confirmo: {accion.descripcion}."),
            Mensaje(rol="asistente", texto=texto),
        ]
        resultado = RespuestaAgente(texto, [], historial)
    return _guardar(sesion_id, sesion, resultado)


def _guardar(sesion_id: str, sesion: Sesion, resultado: RespuestaAgente) -> RespuestaChat:
    sesion.historial = resultado.historial
    sesion.pendiente = resultado.accion_pendiente
    return RespuestaChat(
        respuesta=resultado.texto,
        sesion_id=sesion_id,
        herramientas_usadas=resultado.herramientas_usadas,
        accion_pendiente=resultado.accion_pendiente,
    )


def _normalizar(texto: str) -> str:
    """"¡Sí, confirmo!" -> "si confirmo": minúsculas, sin tildes ni signos."""
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    solo_letras = "".join(c for c in sin_tildes if c.isalnum() or c.isspace())
    return " ".join(solo_letras.split())
