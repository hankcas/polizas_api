"""Piezas compartidas por las pruebas.

Ninguna prueba llama a Gemini ni a la API real: usamos versiones falsas
("dobles de prueba"). Así las pruebas son rápidas, gratis, no gastan cuota
y siempre dan el mismo resultado.
"""

import pytest

from app.agent.llm import LlamadaHerramienta, RespuestaLLM
from app.config import Settings

URL_API = "https://api-falsa.test"


@pytest.fixture
def settings() -> Settings:
    # _env_file=None: las pruebas NO leen tu .env real.
    return Settings(
        _env_file=None,
        polizas_api_url=URL_API,
        polizas_api_key="clave-de-prueba",
        polizas_api_intentos=3,
        gemini_api_key="gemini-de-prueba",
    )


class LLMGuionado:
    """LLM falso: devuelve respuestas escritas de antemano, en orden.

    También guarda lo que recibió en cada llamada, para poder revisarlo.
    """

    def __init__(self, *respuestas: RespuestaLLM):
        self._respuestas = list(respuestas)
        self.llamadas_recibidas: list[list] = []

    def generar(self, sistema, historial, herramientas):
        self.llamadas_recibidas.append(list(historial))
        return self._respuestas.pop(0)


def pide(nombre: str, **argumentos) -> RespuestaLLM:
    """Respuesta del LLM que pide ejecutar una herramienta."""
    return RespuestaLLM(texto="", llamadas=[LlamadaHerramienta(nombre, argumentos)])


def dice(texto: str) -> RespuestaLLM:
    """Respuesta del LLM con texto final."""
    return RespuestaLLM(texto=texto, llamadas=[])
