"""Las herramientas que el agente le ofrece al LLM.

Cada herramienta tiene tres partes que el LLM lee para decidir si la usa:
nombre, descripción y parámetros (en formato JSON Schema). La cuarta parte,
`funcion`, es el código de Python que se ejecuta de verdad; el LLM nunca la ve.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.tools.cliente_api import ClienteApiPolizas

TIPOS_POLIZA = ["INDIVIDUAL", "COLECTIVA"]
ESTADOS_POLIZA = ["ACTIVA", "CANCELADA", "RENOVADA"]


@dataclass
class Herramienta:
    nombre: str
    descripcion: str
    parametros: dict  # JSON Schema: qué argumentos recibe y de qué tipo
    funcion: Callable[..., Any]


def crear_herramientas(cliente: ClienteApiPolizas) -> dict[str, Herramienta]:
    listar_polizas = Herramienta(
        nombre="listar_polizas",
        descripcion=(
            "Lista las pólizas de seguro. Los dos filtros son opcionales; sin filtros "
            "devuelve todas. Cada póliza trae: id, tipo, estado, canonMensual, prima, "
            "porcentajeIpc, fechaInicio, fechaFin y riesgosActivos."
        ),
        parametros={
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": TIPOS_POLIZA,
                    "description": "Tipo de póliza. Una individual cubre un solo riesgo; una colectiva, varios.",
                },
                "estado": {
                    "type": "string",
                    "enum": ESTADOS_POLIZA,
                    "description": "Estado actual de la póliza.",
                },
            },
        },
        funcion=cliente.listar_polizas,
    )
    # Un diccionario nombre -> herramienta: así el agente la encuentra
    # rápido cuando el LLM pide una por su nombre.
    return {h.nombre: h for h in [listar_polizas]}
