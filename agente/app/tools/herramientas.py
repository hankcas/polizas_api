"""Las herramientas que el agente le ofrece al LLM.

Cada herramienta tiene tres partes que el LLM lee para decidir si la usa:
nombre, descripción y parámetros (en formato JSON Schema). La cuarta parte,
`funcion`, es el código de Python que se ejecuta de verdad; el LLM nunca la ve.

Las herramientas que cambian datos (renovar, cancelar) traen además:
- `preparar`: valida y describe la acción ANTES de pedir confirmación.
- `describir_resultado`: arma el mensaje final con los datos reales de la API.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
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
    preparar: Callable[..., str] | None = None
    describir_resultado: Callable[[Any], str] | None = None

    @property
    def requiere_confirmacion(self) -> bool:
        return self.preparar is not None


def pesos(valor: float) -> str:
    """8000000 -> "$8.000.000" (formato colombiano: punto para los miles)."""
    return f"${valor:,.0f}".replace(",", ".")


def fecha(iso: str) -> str:
    """"2026-03-01" -> "01/03/2026"."""
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


def crear_herramientas(cliente: ClienteApiPolizas) -> dict[str, Herramienta]:
    # Esquema reutilizable: un solo parámetro "id" entero.
    parametro_id = {
        "type": "object",
        "properties": {"id": {"type": "integer", "description": "Id de la póliza, por ejemplo 2."}},
        "required": ["id"],
    }

    def preparar(verbo: str) -> Callable[..., str]:
        # Función que fabrica funciones: devuelve un "preparar" para renovar y otro para cancelar.
        def _preparar(id: int) -> str:
            p = cliente.consultar_poliza(id)  # si no existe, la API responde 404 aquí mismo
            return (f"{verbo} la póliza {p['id']} ({p['tipo']}, estado {p['estado']}, "
                    f"vigente hasta {fecha(p['fechaFin'])})")
        return _preparar

    def resultado_poliza(p: dict) -> str:
        return (f"Listo. La póliza {p['id']} ahora está {p['estado']}. "
                f"Vigencia: {fecha(p['fechaInicio'])} a {fecha(p['fechaFin'])}. "
                f"Canon mensual: {pesos(p['canonMensual'])}. Prima: {pesos(p['prima'])}. "
                f"Riesgos activos: {p['riesgosActivos']}.")

    herramientas = [
        Herramienta(
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
        ),
        Herramienta(
            nombre="consultar_poliza",
            descripcion="Consulta el detalle de una póliza por su id.",
            parametros=parametro_id,
            funcion=cliente.consultar_poliza,
        ),
        Herramienta(
            nombre="ver_riesgos",
            descripcion=(
                "Lista los riesgos (bienes asegurados) de una póliza. Cada riesgo trae: id, "
                "descripcion, direccion, valorAsegurado y estado (ACTIVO o CANCELADO)."
            ),
            parametros={
                "type": "object",
                "properties": {"poliza_id": {"type": "integer", "description": "Id de la póliza."}},
                "required": ["poliza_id"],
            },
            funcion=cliente.listar_riesgos,
        ),
        Herramienta(
            nombre="renovar_poliza",
            descripcion=(
                "Renueva una póliza por un año e incrementa el canon y la prima según su IPC. "
                "No se ejecuta de inmediato: queda pendiente hasta que el usuario la confirme."
            ),
            parametros=parametro_id,
            funcion=cliente.renovar_poliza,
            preparar=preparar("Renovar"),
            describir_resultado=resultado_poliza,
        ),
        Herramienta(
            nombre="cancelar_poliza",
            descripcion=(
                "Cancela una póliza y todos sus riesgos. "
                "No se ejecuta de inmediato: queda pendiente hasta que el usuario la confirme."
            ),
            parametros=parametro_id,
            funcion=cliente.cancelar_poliza,
            preparar=preparar("Cancelar"),
            describir_resultado=resultado_poliza,
        ),
    ]
    # Un diccionario nombre -> herramienta: así el agente la encuentra
    # rápido cuando el LLM pide una por su nombre.
    return {h.nombre: h for h in herramientas}
