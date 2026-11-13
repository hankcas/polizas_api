"""El agente: el bucle que conecta al LLM con las herramientas.

1. Le mandamos al LLM la conversación y la lista de herramientas.
2. Si responde con texto, terminamos.
3. Si pide herramientas, las ejecutamos, le devolvemos los resultados y volvemos al paso 1.
"""

from dataclasses import dataclass
from datetime import date

from app.agent.llm import LlamadaHerramienta, Mensaje, ProveedorLLM
from app.tools.cliente_api import ErrorApiPolizas
from app.tools.herramientas import Herramienta

# Tope de vueltas: si el LLM se enreda pidiendo herramientas sin parar,
# cortamos en lugar de quedarnos en un ciclo infinito (y gastando cuota).
MAX_VUELTAS = 6

INSTRUCCIONES = """Eres el asistente de una aseguradora. Respondes en español, de forma breve y clara,
preguntas sobre pólizas de seguro usando las herramientas disponibles.

Reglas:
- Usa siempre las herramientas para obtener datos. Nunca inventes pólizas, valores ni fechas.
- Si una herramienta devuelve un error, explícalo con palabras sencillas y sin inventar datos.
- Escribe los valores en pesos colombianos con separador de miles, por ejemplo $1.500.000.
- Escribe las fechas en formato día/mes/año.
- La fecha de hoy es {hoy}."""


@dataclass
class UsoHerramienta:
    """Registro de una herramienta usada: es la trazabilidad que ve el usuario."""

    nombre: str
    argumentos: dict
    ok: bool
    detalle: str


@dataclass
class RespuestaAgente:
    texto: str
    herramientas_usadas: list[UsoHerramienta]
    historial: list[Mensaje]  # la conversación completa, para la siguiente pregunta


class Agente:
    def __init__(self, llm: ProveedorLLM, herramientas: dict[str, Herramienta]):
        self._llm = llm
        self._herramientas = herramientas

    def responder(self, historial: list[Mensaje], pregunta: str) -> RespuestaAgente:
        # Trabajamos sobre una copia: si algo falla a mitad de camino,
        # la conversación guardada no queda a medias.
        mensajes = [*historial, Mensaje(rol="usuario", texto=pregunta)]
        usadas: list[UsoHerramienta] = []
        instrucciones = INSTRUCCIONES.format(hoy=date.today().strftime("%d/%m/%Y"))

        for _ in range(MAX_VUELTAS):
            respuesta = self._llm.generar(instrucciones, mensajes, list(self._herramientas.values()))
            mensajes.append(
                Mensaje(rol="asistente", texto=respuesta.texto, llamadas=respuesta.llamadas, crudo=respuesta.crudo)
            )

            if not respuesta.llamadas:  # respondió con texto: terminamos
                return RespuestaAgente(respuesta.texto, usadas, mensajes)

            for llamada in respuesta.llamadas:
                resultado, uso = self._ejecutar(llamada)
                usadas.append(uso)
                mensajes.append(
                    Mensaje(rol="herramienta", nombre_herramienta=llamada.nombre, resultado=resultado)
                )

        return RespuestaAgente(
            "No logré completar la respuesta. Intenta con una pregunta más concreta.", usadas, mensajes
        )

    def _ejecutar(self, llamada: LlamadaHerramienta) -> tuple[dict, UsoHerramienta]:
        """Ejecuta una herramienta y devuelve (resultado para el LLM, registro para el usuario).

        Los errores no detienen al agente: se los pasamos al LLM para que se
        los explique al usuario con sus palabras.
        """
        herramienta = self._herramientas.get(llamada.nombre)
        if herramienta is None:
            error = f"La herramienta {llamada.nombre!r} no existe."
            return {"error": error}, UsoHerramienta(llamada.nombre, llamada.argumentos, False, error)

        try:
            # `**` reparte el diccionario como argumentos con nombre:
            # {"tipo": "COLECTIVA"} -> listar_polizas(tipo="COLECTIVA")
            datos = herramienta.funcion(**llamada.argumentos)
        except ErrorApiPolizas as error:
            return {"error": str(error)}, UsoHerramienta(llamada.nombre, llamada.argumentos, False, str(error))
        except TypeError:  # el LLM mandó argumentos que la función no acepta
            error = f"Argumentos inválidos para {llamada.nombre}: {llamada.argumentos}"
            return {"error": error}, UsoHerramienta(llamada.nombre, llamada.argumentos, False, error)

        return {"resultado": datos}, UsoHerramienta(llamada.nombre, llamada.argumentos, True, _resumir(datos))


def _resumir(datos: object) -> str:
    if isinstance(datos, list):
        return f"{len(datos)} resultado(s)"
    return "1 resultado"
