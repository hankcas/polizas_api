"""Pruebas del cliente HTTP: reintentos, 401, errores y POST sin reintento.

`respx` intercepta las peticiones de httpx: ninguna sale a internet.
"""

import httpx
import pytest
import respx

from app.tools.cliente_api import ApiKeyInvalida, ApiNoDisponible, ClienteApiPolizas, ErrorApiPolizas
from tests.conftest import URL_API

POLIZA = {"id": 1, "tipo": "INDIVIDUAL", "estado": "ACTIVA"}


@pytest.fixture
def esperas() -> list[float]:
    return []


@pytest.fixture
def cliente(settings, esperas) -> ClienteApiPolizas:
    # En lugar de time.sleep, anotamos cuánto habría esperado: la prueba no se demora.
    return ClienteApiPolizas(settings, esperar=esperas.append)


@respx.mock
def test_listar_envia_filtros_y_api_key(cliente):
    ruta = respx.get(f"{URL_API}/polizas").respond(json=[POLIZA])

    assert cliente.listar_polizas(tipo="COLECTIVA") == [POLIZA]

    peticion = ruta.calls.last.request
    assert peticion.url.params["tipo"] == "COLECTIVA"
    assert "estado" not in peticion.url.params  # el filtro vacío no se manda
    assert peticion.headers["x-api-key"] == "clave-de-prueba"


@respx.mock
def test_reintenta_si_la_api_esta_dormida(cliente, esperas):
    respx.get(f"{URL_API}/polizas/1").mock(
        side_effect=[httpx.ReadTimeout("dormida"), httpx.Response(503), httpx.Response(200, json=POLIZA)]
    )

    assert cliente.consultar_poliza(1) == POLIZA
    assert esperas == [2, 4]  # espera creciente entre intentos


@respx.mock
def test_se_rinde_despues_de_todos_los_intentos(cliente, esperas):
    ruta = respx.get(f"{URL_API}/polizas").mock(side_effect=httpx.ConnectError("sin red"))

    with pytest.raises(ApiNoDisponible, match="3 intentos"):
        cliente.listar_polizas()
    assert ruta.call_count == 3


@respx.mock
def test_401_no_se_reintenta(cliente):
    ruta = respx.get(f"{URL_API}/polizas").respond(401)

    with pytest.raises(ApiKeyInvalida, match="POLIZAS_API_KEY"):
        cliente.listar_polizas()
    assert ruta.call_count == 1  # con la misma clave fallaría igual


@respx.mock
def test_error_de_negocio_trae_el_mensaje_de_la_api(cliente):
    respx.get(f"{URL_API}/polizas/99").respond(404, json={"mensaje": "No existe la póliza con id 99"})

    with pytest.raises(ErrorApiPolizas, match="No existe la póliza con id 99"):
        cliente.consultar_poliza(99)


@respx.mock
def test_id_decimal_del_llm_se_convierte_a_entero(cliente):
    ruta = respx.get(f"{URL_API}/polizas/2/riesgos").respond(json=[])

    cliente.listar_riesgos(2.0)  # Gemini a veces manda los enteros como 2.0
    assert ruta.called


@respx.mock
def test_post_despierta_la_api_y_no_se_reintenta(cliente):
    salud = respx.get(f"{URL_API}/actuator/health").respond(json={"status": "UP"})
    renovar = respx.post(f"{URL_API}/polizas/1/renovar").mock(side_effect=httpx.ReadTimeout("lento"))

    with pytest.raises(ApiNoDisponible, match="no sé si el cambio se aplicó"):
        cliente.renovar_poliza(1)
    assert salud.called  # primero despertó la API con una lectura segura
    assert renovar.call_count == 1  # y el POST se mandó UNA sola vez
