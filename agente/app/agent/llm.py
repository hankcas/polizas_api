"""El "idioma común" entre el agente y cualquier proveedor de LLM.

El agente nunca habla directamente con Gemini: usa estas clases. Cada proveedor
(hoy Gemini, mañana otro) tiene un adaptador que traduce entre este formato y
el de su SDK. Así, cambiar de proveedor no obliga a tocar el agente.
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from app.config import Settings
from app.tools.herramientas import Herramienta


@dataclass
class LlamadaHerramienta:
    """El LLM pide ejecutar una herramienta con ciertos argumentos."""

    nombre: str
    argumentos: dict


@dataclass
class Mensaje:
    """Un mensaje de la conversación.

    - "usuario": lo que escribió la persona (`texto`).
    - "asistente": lo que respondió el LLM (`texto` y/o `llamadas`).
    - "herramienta": el resultado de ejecutar una herramienta.
    """

    rol: Literal["usuario", "asistente", "herramienta"]
    texto: str = ""
    llamadas: list[LlamadaHerramienta] = field(default_factory=list)
    nombre_herramienta: str = ""
    resultado: dict | None = None
    # Contenido original del proveedor. Gemini 3 exige que le reenviemos su
    # respuesta tal cual (incluye una "firma de pensamiento"); el agente no
    # mira este campo, solo lo guarda.
    crudo: Any = None


@dataclass
class RespuestaLLM:
    texto: str
    llamadas: list[LlamadaHerramienta]
    crudo: Any = None


class ErrorLLM(Exception):
    """El proveedor de LLM falló, con un mensaje para el usuario."""


class ProveedorLLM(Protocol):
    """Lo único que el agente necesita de un LLM: este método.

    `Protocol` significa "cualquier clase que tenga este método sirve",
    sin necesidad de heredar de nada. En las pruebas usaremos un LLM falso.
    """

    def generar(
        self, sistema: str, historial: list[Mensaje], herramientas: list[Herramienta]
    ) -> RespuestaLLM: ...


def crear_proveedor(settings: Settings) -> ProveedorLLM:
    """Elige el adaptador según LLM_PROVIDER del .env."""
    if settings.llm_provider == "gemini":
        from app.agent.gemini import ProveedorGemini

        if settings.gemini_api_key is None:
            raise ValueError("Falta GEMINI_API_KEY en el archivo .env.")
        return ProveedorGemini(settings.gemini_api_key.get_secret_value(), settings.llm_model)
    raise ValueError(f"Proveedor de LLM no soportado: {settings.llm_provider!r}")
