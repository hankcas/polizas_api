"""Adaptador de Google Gemini: traduce entre nuestro formato y el SDK google-genai."""

import logging

from google import genai
from google.genai import errors, types

from app.agent.llm import ErrorLLM, LlamadaHerramienta, Mensaje, RespuestaLLM
from app.tools.herramientas import Herramienta

log = logging.getLogger(__name__)


class ProveedorGemini:
    def __init__(
        self, api_key: str, modelo: str, respaldo: str | None = None, cliente: genai.Client | None = None
    ):
        # Lista de modelos a intentar en orden: el principal y, si hay, el de respaldo.
        self._modelos = [modelo, respaldo] if respaldo else [modelo]
        self._cliente = cliente or genai.Client(
            api_key=api_key,
            # El SDK reintenta solo si Gemini responde 429 (límite) o 5xx (saturado).
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=3, initial_delay=2, max_delay=10)
            ),
        )

    def generar(
        self, sistema: str, historial: list[Mensaje], herramientas: list[Herramienta]
    ) -> RespuestaLLM:
        config = types.GenerateContentConfig(
            system_instruction=sistema,
            tools=[types.Tool(function_declarations=[_declaracion(h) for h in herramientas])],
            # Nosotros ejecutamos las herramientas, no el SDK: así controlamos
            # la trazabilidad y, en la etapa 3, la confirmación.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        contenidos = _a_contenidos(historial)
        for modelo in self._modelos:
            try:
                respuesta = self._cliente.models.generate_content(model=modelo, contents=contenidos, config=config)
                break  # funcionó: salimos del for
            except errors.ServerError as error:  # 5xx: el modelo está saturado
                ultimo_error = error
                log.warning("El modelo %s está saturado (%s); probando el siguiente.", modelo, error.code)
            except errors.APIError as error:  # otros errores (clave, cuota...): cambiar de modelo no ayuda
                raise ErrorLLM(_mensaje_de_error(error)) from error
        else:
            # El `else` de un `for` corre solo si el for terminó sin `break`:
            # es decir, todos los modelos fallaron.
            raise ErrorLLM(_mensaje_de_error(ultimo_error)) from ultimo_error

        contenido = respuesta.candidates[0].content if respuesta.candidates else None
        if contenido is None or not contenido.parts:
            return RespuestaLLM(texto="No pude generar una respuesta. Intenta reformular la pregunta.", llamadas=[])

        texto = "".join(p.text for p in contenido.parts if p.text and not p.thought)
        llamadas = [
            LlamadaHerramienta(nombre=p.function_call.name, argumentos=dict(p.function_call.args or {}))
            for p in contenido.parts
            if p.function_call
        ]
        return RespuestaLLM(texto=texto, llamadas=llamadas, crudo=contenido)


def _declaracion(herramienta: Herramienta) -> types.FunctionDeclaration:
    return types.FunctionDeclaration(
        name=herramienta.nombre,
        description=herramienta.descripcion,
        parameters_json_schema=herramienta.parametros,
    )


def _a_contenidos(historial: list[Mensaje]) -> list[types.Content]:
    """Convierte nuestro historial al formato de Gemini.

    Gemini usa dos roles: "user" (persona y resultados de herramientas)
    y "model" (el LLM). Los resultados seguidos de varias herramientas
    van juntos en un solo contenido.
    """
    contenidos: list[types.Content] = []
    for mensaje in historial:
        if mensaje.rol == "usuario":
            contenidos.append(types.Content(role="user", parts=[types.Part(text=mensaje.texto)]))

        elif mensaje.rol == "asistente":
            if isinstance(mensaje.crudo, types.Content):
                contenidos.append(mensaje.crudo)  # tal cual, con su firma de pensamiento
            else:
                partes = [types.Part(text=mensaje.texto)] if mensaje.texto else []
                partes += [
                    types.Part(function_call=types.FunctionCall(name=ll.nombre, args=ll.argumentos))
                    for ll in mensaje.llamadas
                ]
                contenidos.append(types.Content(role="model", parts=partes))

        else:  # "herramienta"
            parte = types.Part.from_function_response(
                name=mensaje.nombre_herramienta, response=mensaje.resultado or {}
            )
            anterior = contenidos[-1] if contenidos else None
            if anterior is not None and anterior.role == "user" and anterior.parts[0].function_response:
                anterior.parts.append(parte)
            else:
                contenidos.append(types.Content(role="user", parts=[parte]))
    return contenidos


def _mensaje_de_error(error: errors.APIError) -> str:
    if error.code == 429:
        return ("Se agotó por ahora la cuota gratuita de Gemini (límite por minuto o por día). "
                "Espera un momento y vuelve a intentar.")
    if error.code in (401, 403) or (error.code == 400 and "API key" in str(error.message)):
        return "Gemini rechazó la clave. Revisa GEMINI_API_KEY en el archivo .env."
    if error.code and error.code >= 500:
        return "Gemini está saturado en este momento. Intenta de nuevo en unos segundos."
    return f"Error de Gemini ({error.code}): {error.message}"
