"""Pruebas del bucle del agente con un LLM falso y herramientas falsas."""

from app.agent.agente import MAX_VUELTAS, AccionPendiente, Agente
from app.tools.cliente_api import ErrorApiPolizas
from app.tools.herramientas import Herramienta
from tests.conftest import LLMGuionado, dice, pide


class Registro:
    """Anota cada vez que se ejecuta una herramienta falsa."""

    def __init__(self):
        self.llamadas: list[tuple[str, dict]] = []


def herramientas_falsas(registro: Registro) -> dict[str, Herramienta]:
    def listar_polizas(tipo=None, estado=None):
        registro.llamadas.append(("listar_polizas", {"tipo": tipo, "estado": estado}))
        return [{"id": 2, "tipo": "COLECTIVA"}, {"id": 5, "tipo": "COLECTIVA"}]

    def consultar_poliza(id):
        registro.llamadas.append(("consultar_poliza", {"id": id}))
        raise ErrorApiPolizas(f"No existe la póliza con id {id}")

    def renovar_poliza(id):
        registro.llamadas.append(("renovar_poliza", {"id": id}))
        return {"id": id, "estado": "RENOVADA"}

    def preparar_renovacion(id):
        if id == 99:
            raise ErrorApiPolizas("No existe la póliza con id 99")
        return f"Renovar la póliza {id}"

    sin_parametros = {"type": "object", "properties": {}}
    return {
        "listar_polizas": Herramienta("listar_polizas", "Lista pólizas", sin_parametros, listar_polizas),
        "consultar_poliza": Herramienta("consultar_poliza", "Consulta", sin_parametros, consultar_poliza),
        "renovar_poliza": Herramienta(
            "renovar_poliza", "Renueva", sin_parametros, renovar_poliza,
            preparar=preparar_renovacion,
            describir_resultado=lambda p: f"Listo. La póliza {p['id']} ahora está {p['estado']}.",
        ),
    }


def test_usa_la_herramienta_y_registra_la_trazabilidad():
    registro = Registro()
    llm = LLMGuionado(pide("listar_polizas", tipo="COLECTIVA"), dice("Hay 2 pólizas colectivas."))

    respuesta = Agente(llm, herramientas_falsas(registro)).responder([], "¿Qué pólizas colectivas hay?")

    assert respuesta.texto == "Hay 2 pólizas colectivas."
    assert registro.llamadas == [("listar_polizas", {"tipo": "COLECTIVA", "estado": None})]
    [uso] = respuesta.herramientas_usadas
    assert (uso.nombre, uso.estado, uso.detalle) == ("listar_polizas", "ok", "2 resultado(s)")
    # El segundo turno del LLM recibió el resultado de la herramienta.
    ultimo = llm.llamadas_recibidas[1][-1]
    assert ultimo.rol == "herramienta" and ultimo.resultado["resultado"][0]["id"] == 2


def test_un_error_de_la_api_se_le_pasa_al_llm_sin_romper_el_agente():
    llm = LLMGuionado(pide("consultar_poliza", id=99), dice("Esa póliza no existe."))

    respuesta = Agente(llm, herramientas_falsas(Registro())).responder([], "¿Y la póliza 99?")

    assert respuesta.herramientas_usadas[0].estado == "error"
    assert llm.llamadas_recibidas[1][-1].resultado == {"error": "No existe la póliza con id 99"}
    assert respuesta.texto == "Esa póliza no existe."


def test_herramienta_inexistente():
    llm = LLMGuionado(pide("borrar_todo"), dice("No puedo hacer eso."))

    respuesta = Agente(llm, herramientas_falsas(Registro())).responder([], "Borra todo")

    assert respuesta.herramientas_usadas[0].estado == "error"
    assert "no existe" in respuesta.herramientas_usadas[0].detalle


def test_corta_si_el_llm_no_deja_de_pedir_herramientas():
    llm = LLMGuionado(*[pide("listar_polizas") for _ in range(MAX_VUELTAS)])

    respuesta = Agente(llm, herramientas_falsas(Registro())).responder([], "¿?")

    assert len(llm.llamadas_recibidas) == MAX_VUELTAS
    assert "No logré completar" in respuesta.texto


def test_renovar_queda_pendiente_y_NO_se_ejecuta():
    """La regla más importante: el LLM pide renovar, pero no se toca la API."""
    registro = Registro()
    llm = LLMGuionado(pide("renovar_poliza", id=1), dice("¿Confirmas la renovación?"))

    respuesta = Agente(llm, herramientas_falsas(registro)).responder([], "Renueva la póliza 1")

    assert registro.llamadas == []  # renovar_poliza NO se llamó
    assert respuesta.accion_pendiente.descripcion == "Renovar la póliza 1"
    assert respuesta.herramientas_usadas[0].estado == "pendiente"
    assert "NO se ha ejecutado" in llm.llamadas_recibidas[1][-1].resultado["importante"]


def test_si_no_existe_la_poliza_no_se_ofrece_confirmar():
    llm = LLMGuionado(pide("renovar_poliza", id=99), dice("La póliza 99 no existe."))

    respuesta = Agente(llm, herramientas_falsas(Registro())).responder([], "Renueva la 99")

    assert respuesta.accion_pendiente is None
    assert respuesta.herramientas_usadas[0].estado == "error"


def test_solo_una_accion_pendiente_por_turno():
    llm = LLMGuionado(
        pide("renovar_poliza", id=1), pide("renovar_poliza", id=2), dice("Confirma la primera.")
    )

    respuesta = Agente(llm, herramientas_falsas(Registro())).responder([], "Renueva la 1 y la 2")

    assert respuesta.accion_pendiente.argumentos == {"id": 1}
    assert [u.estado for u in respuesta.herramientas_usadas] == ["pendiente", "error"]


def test_ejecutar_confirmada_llama_a_la_api_sin_pasar_por_el_llm():
    registro = Registro()
    agente = Agente(LLMGuionado(), herramientas_falsas(registro))  # LLM sin respuestas: no debe usarse
    accion = AccionPendiente("abc", "renovar_poliza", {"id": 1}, "Renovar la póliza 1")

    respuesta = agente.ejecutar_confirmada([], accion)

    assert registro.llamadas == [("renovar_poliza", {"id": 1})]
    assert respuesta.texto == "Listo. La póliza 1 ahora está RENOVADA."  # texto armado por el código
    assert [m.rol for m in respuesta.historial] == ["usuario", "asistente"]


def test_la_conversacion_guardada_no_cambia_si_falla_a_mitad():
    historial = []

    class LLMQueFalla:
        def generar(self, *args):
            raise RuntimeError("se cayó")

    try:
        Agente(LLMQueFalla(), herramientas_falsas(Registro())).responder(historial, "hola")
    except RuntimeError:
        pass
    assert historial == []  # el agente trabajó sobre una copia
