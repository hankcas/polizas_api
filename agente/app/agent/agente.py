"""El agente: el bucle que conecta al LLM con las herramientas.

1. Le mandamos al LLM la conversación y la lista de herramientas.
2. Si responde con texto, terminamos.
3. Si pide herramientas, las ejecutamos, le devolvemos los resultados y volvemos al paso 1.

Excepción: las herramientas que cambian datos (renovar, cancelar) NO se
ejecutan en el bucle. Quedan como "acción pendiente" y solo se ejecutan con
`ejecutar_confirmada`, cuando el usuario confirma. La regla está en el código:
aunque el LLM se equivoque, no puede cambiar datos por su cuenta.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Literal

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
- Si el usuario pide renovar o cancelar una póliza, llama directamente a la herramienta: el sistema
  deja la acción pendiente y le muestra al usuario un botón para confirmarla. Después pídele que
  confirme. Nunca digas que una póliza fue renovada o cancelada: eso lo informa el sistema.
- Para preguntas sobre coberturas, exclusiones, plazos o procedimientos del seguro, usa
  buscar_condiciones. Responde solo con lo que digan los fragmentos y cita la cláusula y la página
  (por ejemplo: "según la cláusula 6, página 1"). Si los fragmentos no lo responden, dilo.
- Escribe los valores en pesos colombianos con separador de miles, por ejemplo $1.500.000.
- Escribe las fechas en formato día/mes/año.
- La fecha de hoy es {hoy}."""


@dataclass
class UsoHerramienta:
    """Registro de una herramienta usada: es la trazabilidad que ve el usuario."""

    nombre: str
    argumentos: dict
    estado: Literal["ok", "error", "pendiente"]
    detalle: str


@dataclass
class AccionPendiente:
    """Un cambio que el LLM pidió y que espera la confirmación del usuario."""

    id: str
    herramienta: str
    argumentos: dict
    descripcion: str


@dataclass
class RespuestaAgente:
    texto: str
    herramientas_usadas: list[UsoHerramienta]
    historial: list[Mensaje]  # la conversación completa, para la siguiente pregunta
    accion_pendiente: AccionPendiente | None = None


class Agente:
    def __init__(self, llm: ProveedorLLM, herramientas: dict[str, Herramienta]):
        self._llm = llm
        self._herramientas = herramientas

    def responder(self, historial: list[Mensaje], pregunta: str) -> RespuestaAgente:
        # Trabajamos sobre una copia: si algo falla a mitad de camino,
        # la conversación guardada no queda a medias.
        mensajes = [*historial, Mensaje(rol="usuario", texto=pregunta)]
        usadas: list[UsoHerramienta] = []
        pendiente: AccionPendiente | None = None
        instrucciones = INSTRUCCIONES.format(hoy=date.today().strftime("%d/%m/%Y"))

        for _ in range(MAX_VUELTAS):
            respuesta = self._llm.generar(instrucciones, mensajes, list(self._herramientas.values()))
            mensajes.append(
                Mensaje(rol="asistente", texto=respuesta.texto, llamadas=respuesta.llamadas, crudo=respuesta.crudo)
            )

            if not respuesta.llamadas:  # respondió con texto: terminamos
                texto = respuesta.texto
                if pendiente and not texto:
                    texto = f"¿Confirmas esta acción? {pendiente.descripcion}."
                return RespuestaAgente(texto, usadas, mensajes, pendiente)

            for llamada in respuesta.llamadas:
                herramienta = self._herramientas.get(llamada.nombre)
                if herramienta is not None and herramienta.requiere_confirmacion:
                    resultado, uso, nueva = self._preparar(herramienta, llamada, pendiente)
                    pendiente = nueva or pendiente
                else:
                    resultado, uso = self._ejecutar(herramienta, llamada)
                usadas.append(uso)
                mensajes.append(
                    Mensaje(rol="herramienta", nombre_herramienta=llamada.nombre, resultado=resultado)
                )

        return RespuestaAgente(
            "No logré completar la respuesta. Intenta con una pregunta más concreta.", usadas, mensajes, pendiente
        )

    def ejecutar_confirmada(self, historial: list[Mensaje], accion: AccionPendiente) -> RespuestaAgente:
        """Ejecuta una acción que el usuario ya confirmó.

        No pasa por el LLM: el mensaje final lo arma el código con la respuesta
        real de la API, así el modelo no puede "inventar" que algo se hizo.
        """
        herramienta = self._herramientas[accion.herramienta]
        try:
            datos = herramienta.funcion(**accion.argumentos)
        except ErrorApiPolizas as error:
            texto = f"No se pudo completar la acción: {error}"
            uso = UsoHerramienta(accion.herramienta, accion.argumentos, "error", str(error))
        else:
            texto = herramienta.describir_resultado(datos)
            uso = UsoHerramienta(accion.herramienta, accion.argumentos, "ok", "Ejecutada tras confirmación")

        # Dejamos constancia en la conversación para que el LLM lo sepa en las siguientes preguntas.
        mensajes = [
            *historial,
            Mensaje(rol="usuario", texto=f"Confirmo: {accion.descripcion}."),
            Mensaje(rol="asistente", texto=texto),
        ]
        return RespuestaAgente(texto, [uso], mensajes)

    def _preparar(
        self, herramienta: Herramienta, llamada: LlamadaHerramienta, ya_pendiente: AccionPendiente | None
    ) -> tuple[dict, UsoHerramienta, AccionPendiente | None]:
        """Deja una acción pendiente en lugar de ejecutarla."""
        if ya_pendiente is not None:
            error = "Solo se puede preparar una acción a la vez. Pide al usuario que confirme la primera."
            return {"error": error}, UsoHerramienta(llamada.nombre, llamada.argumentos, "error", error), None
        try:
            descripcion = herramienta.preparar(**llamada.argumentos)
        except (ErrorApiPolizas, TypeError) as error:
            return {"error": str(error)}, UsoHerramienta(llamada.nombre, llamada.argumentos, "error", str(error)), None

        accion = AccionPendiente(str(uuid.uuid4()), llamada.nombre, llamada.argumentos, descripcion)
        resultado = {
            "pendiente_de_confirmacion": descripcion,
            "importante": "La acción NO se ha ejecutado. Pide al usuario que la confirme.",
        }
        uso = UsoHerramienta(llamada.nombre, llamada.argumentos, "pendiente", "Esperando confirmación del usuario")
        return resultado, uso, accion

    def _ejecutar(
        self, herramienta: Herramienta | None, llamada: LlamadaHerramienta
    ) -> tuple[dict, UsoHerramienta]:
        """Ejecuta una herramienta de solo lectura y devuelve (resultado para el LLM, registro para el usuario).

        Los errores no detienen al agente: se los pasamos al LLM para que se
        los explique al usuario con sus palabras.
        """
        if herramienta is None:
            error = f"La herramienta {llamada.nombre!r} no existe."
            return {"error": error}, UsoHerramienta(llamada.nombre, llamada.argumentos, "error", error)

        try:
            # `**` reparte el diccionario como argumentos con nombre:
            # {"tipo": "COLECTIVA"} -> listar_polizas(tipo="COLECTIVA")
            datos = herramienta.funcion(**llamada.argumentos)
        except ErrorApiPolizas as error:
            return {"error": str(error)}, UsoHerramienta(llamada.nombre, llamada.argumentos, "error", str(error))
        except TypeError:  # el LLM mandó argumentos que la función no acepta
            error = f"Argumentos inválidos para {llamada.nombre}: {llamada.argumentos}"
            return {"error": error}, UsoHerramienta(llamada.nombre, llamada.argumentos, "error", error)

        resumen = herramienta.resumir(datos) if herramienta.resumir else _resumir(datos)
        return {"resultado": datos}, UsoHerramienta(llamada.nombre, llamada.argumentos, "ok", resumen)


def _resumir(datos: object) -> str:
    if isinstance(datos, list):
        return f"{len(datos)} resultado(s)"
    return "1 resultado"
