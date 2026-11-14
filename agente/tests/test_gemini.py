"""Pruebas del adaptador de Gemini con un cliente falso: no se llama a Google."""

from types import SimpleNamespace

import pytest
from google.genai import errors, types

from app.agent.gemini import ProveedorGemini, _a_contenidos
from app.agent.llm import ErrorLLM, LlamadaHerramienta, Mensaje


def error_api(codigo: int) -> errors.APIError:
    clase = errors.ServerError if codigo >= 500 else errors.ClientError
    return clase(codigo, {"error": {"code": codigo, "message": "falso", "status": "X"}})


def respuesta_texto(texto: str) -> types.GenerateContentResponse:
    contenido = types.Content(role="model", parts=[types.Part(text=texto)])
    return types.GenerateContentResponse(candidates=[types.Candidate(content=contenido)])


class ModelosFalsos:
    """Imita `cliente.models`: cada modelo responde texto o lanza el error indicado."""

    def __init__(self, errores_por_modelo: dict[str, int]):
        self._errores = errores_por_modelo
        self.usados: list[str] = []

    def generate_content(self, model, contents, config):
        self.usados.append(model)
        if model in self._errores:
            raise error_api(self._errores[model])
        return respuesta_texto(f"respondió {model}")


def proveedor(errores: dict[str, int]) -> tuple[ProveedorGemini, ModelosFalsos]:
    modelos = ModelosFalsos(errores)
    p = ProveedorGemini("clave", "principal", ["respaldo1", "respaldo2"], cliente=SimpleNamespace(models=modelos))
    return p, modelos


def generar(p: ProveedorGemini) -> str:
    return p.generar("instrucciones", [Mensaje(rol="usuario", texto="hola")], []).texto


@pytest.mark.parametrize("codigo", [429, 503])
def test_si_el_principal_falla_usa_el_respaldo(codigo):
    p, modelos = proveedor({"principal": codigo})

    assert generar(p) == "respondió respaldo1"
    assert modelos.usados == ["principal", "respaldo1"]


def test_si_todos_agotaron_la_cuota_explica_el_limite():
    p, modelos = proveedor({"principal": 429, "respaldo1": 429, "respaldo2": 429})

    with pytest.raises(ErrorLLM, match="cuota gratuita"):
        generar(p)
    assert len(modelos.usados) == 3


def test_clave_invalida_no_prueba_otros_modelos():
    p, modelos = proveedor({"principal": 403})

    with pytest.raises(ErrorLLM, match="GEMINI_API_KEY"):
        generar(p)
    assert modelos.usados == ["principal"]  # otro modelo fallaría igual


def test_resultados_seguidos_de_herramientas_van_juntos():
    historial = [
        Mensaje(rol="usuario", texto="¿pólizas 1 y 2?"),
        Mensaje(rol="asistente", llamadas=[LlamadaHerramienta("consultar_poliza", {"id": 1}),
                                           LlamadaHerramienta("consultar_poliza", {"id": 2})]),
        Mensaje(rol="herramienta", nombre_herramienta="consultar_poliza", resultado={"resultado": {"id": 1}}),
        Mensaje(rol="herramienta", nombre_herramienta="consultar_poliza", resultado={"resultado": {"id": 2}}),
    ]

    contenidos = _a_contenidos(historial)

    assert [c.role for c in contenidos] == ["user", "model", "user"]
    assert len(contenidos[2].parts) == 2  # las dos respuestas en un solo turno


def test_reenvia_el_contenido_original_con_su_firma():
    original = types.Content(role="model", parts=[types.Part(text="hola", thought_signature=b"firma")])

    contenidos = _a_contenidos([Mensaje(rol="asistente", texto="hola", crudo=original)])

    assert contenidos[0] is original  # tal cual, sin reconstruirlo
