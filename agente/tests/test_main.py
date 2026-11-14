"""Pruebas de los endpoints de FastAPI: /chat, confirmación con botón y con "sí"/"no"."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.agent.agente import Agente
from app.agent.llm import ErrorLLM
from tests.conftest import LLMGuionado, dice, pide
from tests.test_agente import Registro, herramientas_falsas


@pytest.fixture
def armar(monkeypatch):
    """Devuelve una función que monta la app con un LLM guionado y herramientas falsas."""
    monkeypatch.setattr(main, "_sesiones", {})  # cada prueba empieza sin conversaciones
    registro = Registro()

    def _armar(*respuestas_llm):
        agente = Agente(LLMGuionado(*respuestas_llm), herramientas_falsas(registro))
        # dependency_overrides: FastAPI usa este agente en lugar del real.
        main.app.dependency_overrides[main.obtener_agente] = lambda: agente
        return TestClient(main.app), registro

    yield _armar
    main.app.dependency_overrides.clear()


def pedir_renovacion(cliente) -> dict:
    datos = cliente.post("/chat", json={"mensaje": "Renueva la póliza 1"}).json()
    assert datos["accion_pendiente"]["descripcion"] == "Renovar la póliza 1"
    return datos


def test_chat_responde_con_trazabilidad(armar):
    cliente, _ = armar(pide("listar_polizas"), dice("Hay 2 pólizas."))

    r = cliente.post("/chat", json={"mensaje": "¿Cuántas pólizas hay?"})

    assert r.status_code == 200
    datos = r.json()
    assert datos["respuesta"] == "Hay 2 pólizas."
    assert datos["sesion_id"]
    assert datos["herramientas_usadas"][0]["nombre"] == "listar_polizas"


def test_mensaje_vacio_es_rechazado(armar):
    cliente, _ = armar()
    assert cliente.post("/chat", json={"mensaje": ""}).status_code == 422


def test_boton_confirmar_ejecuta_la_accion(armar):
    cliente, registro = armar(pide("renovar_poliza", id=1), dice("¿Confirmas?"))
    datos = pedir_renovacion(cliente)
    assert registro.llamadas == []  # todavía nada

    r = cliente.post("/chat/confirmar", json={
        "sesion_id": datos["sesion_id"], "accion_id": datos["accion_pendiente"]["id"], "confirmar": True,
    })

    assert r.json()["respuesta"] == "Listo. La póliza 1 ahora está RENOVADA."
    assert registro.llamadas == [("renovar_poliza", {"id": 1})]


def test_la_confirmacion_sirve_una_sola_vez(armar):
    cliente, registro = armar(pide("renovar_poliza", id=1), dice("¿Confirmas?"))
    datos = pedir_renovacion(cliente)
    cuerpo = {"sesion_id": datos["sesion_id"], "accion_id": datos["accion_pendiente"]["id"], "confirmar": True}

    cliente.post("/chat/confirmar", json=cuerpo)
    segunda = cliente.post("/chat/confirmar", json=cuerpo)

    assert segunda.status_code == 409
    assert len(registro.llamadas) == 1  # no se renovó dos veces


@pytest.mark.parametrize("respuesta", ["Sí", "¡sí, confirmo!", "dale"])
def test_escribir_si_confirma(armar, respuesta):
    cliente, registro = armar(pide("renovar_poliza", id=1), dice("¿Confirmas?"))
    datos = pedir_renovacion(cliente)

    cliente.post("/chat", json={"mensaje": respuesta, "sesion_id": datos["sesion_id"]})

    assert registro.llamadas == [("renovar_poliza", {"id": 1})]


def test_escribir_no_descarta(armar):
    cliente, registro = armar(pide("renovar_poliza", id=1), dice("¿Confirmas?"))
    datos = pedir_renovacion(cliente)

    r = cliente.post("/chat", json={"mensaje": "No", "sesion_id": datos["sesion_id"]})

    assert r.json()["respuesta"] == "Entendido, no hice ningún cambio."
    assert registro.llamadas == []


def test_otro_mensaje_descarta_la_accion_pendiente(armar):
    cliente, registro = armar(pide("renovar_poliza", id=1), dice("¿Confirmas?"), dice("Hola."), dice("¿Sí qué?"))
    datos = pedir_renovacion(cliente)
    sesion = datos["sesion_id"]

    cliente.post("/chat", json={"mensaje": "Mejor dime hola", "sesion_id": sesion})
    cliente.post("/chat", json={"mensaje": "sí", "sesion_id": sesion})  # este "sí" llega tarde

    assert registro.llamadas == []  # nunca se renovó


def test_error_del_llm_responde_503(armar):
    cliente, _ = armar()

    class LLMSinCuota:
        def generar(self, *args):
            raise ErrorLLM("Se agotó la cuota gratuita de Gemini")

    main.app.dependency_overrides[main.obtener_agente] = lambda: Agente(LLMSinCuota(), {})
    r = cliente.post("/chat", json={"mensaje": "hola"})

    assert r.status_code == 503
    assert "cuota" in r.json()["detail"]
