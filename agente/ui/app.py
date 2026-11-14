"""Interfaz de chat (Streamlit) para el agente de pólizas.

La interfaz no tiene lógica de IA: solo le habla a la API del agente
(POST /chat y POST /chat/confirmar) y muestra lo que responde.

Streamlit vuelve a ejecutar este archivo completo cada vez que el usuario hace
algo (escribe, hace clic). Por eso lo que debe sobrevivir entre ejecuciones
(la conversación, la acción pendiente) se guarda en `st.session_state`.

Uso, desde la carpeta agente/ y con el agente corriendo:
    streamlit run ui/app.py
"""

import os

import httpx
import streamlit as st

AGENTE_URL = os.getenv("AGENTE_URL", "http://localhost:8000")
TIMEOUT = 300  # segundos: la API de pólizas puede tardar ~2,5 min en despertar

EJEMPLOS = [
    "¿Qué pólizas colectivas están activas?",
    "¿Qué riesgos tiene la póliza 2?",
    "¿Qué no cubre el seguro?",
    "Si renuevo la póliza 5, ¿en cuánto quedaría el canon?",
    "Renueva la póliza 4",
]
ICONOS = {"ok": "✅", "error": "❌", "pendiente": "⏳"}

st.set_page_config(page_title="Agente de pólizas", page_icon="🛡️")


def iniciar_estado() -> None:
    st.session_state.setdefault("sesion_id", None)
    st.session_state.setdefault("mensajes", [])  # [{"rol", "texto", "herramientas"}]
    st.session_state.setdefault("pendiente", None)
    st.session_state.setdefault("error", None)


def llamar_agente(ruta: str, cuerpo: dict) -> dict | None:
    """Llama a la API del agente. Si falla, guarda el error para mostrarlo y devuelve None."""
    try:
        respuesta = httpx.post(f"{AGENTE_URL}{ruta}", json=cuerpo, timeout=TIMEOUT)
    except httpx.ConnectError:
        st.session_state.error = f"No me pude conectar con el agente en {AGENTE_URL}. ¿Está corriendo?"
        return None
    except httpx.TimeoutException:
        st.session_state.error = "El agente tardó demasiado en responder. Intenta de nuevo."
        return None
    if respuesta.status_code != 200:
        try:
            detalle = respuesta.json().get("detail")
        except ValueError:
            detalle = None
        st.session_state.error = detalle or f"El agente respondió con error HTTP {respuesta.status_code}."
        return None
    return respuesta.json()


def guardar_respuesta(datos: dict) -> None:
    st.session_state.sesion_id = datos["sesion_id"]
    st.session_state.pendiente = datos.get("accion_pendiente")
    st.session_state.mensajes.append(
        {"rol": "assistant", "texto": datos["respuesta"], "herramientas": datos["herramientas_usadas"]}
    )


def mostrar_herramientas(herramientas: list[dict]) -> None:
    """La trazabilidad: qué herramientas usó el agente para responder."""
    if not herramientas:
        return
    with st.expander(f"🔧 Herramientas usadas ({len(herramientas)})"):
        for h in herramientas:
            argumentos = ", ".join(f"{k}={v!r}" for k, v in h["argumentos"].items())
            st.markdown(f"{ICONOS.get(h['estado'], '•')} `{h['nombre']}({argumentos})` — {h['detalle']}")


def preguntar(texto: str) -> None:
    st.session_state.error = None
    st.session_state.mensajes.append({"rol": "user", "texto": texto})
    with st.chat_message("user"):
        st.markdown(texto)
    with st.chat_message("assistant"), st.spinner("Pensando… si la API de pólizas está dormida, puede tardar hasta 3 minutos."):
        datos = llamar_agente("/chat", {"mensaje": texto, "sesion_id": st.session_state.sesion_id})
    if datos:
        guardar_respuesta(datos)


def resolver_pendiente(confirmar: bool) -> None:
    accion = st.session_state.pendiente
    st.session_state.error = None
    st.session_state.pendiente = None
    st.session_state.mensajes.append({"rol": "user", "texto": "✅ Confirmo" if confirmar else "✖️ No, cancelar"})
    with st.spinner("Ejecutando…" if confirmar else "Descartando…"):
        datos = llamar_agente(
            "/chat/confirmar",
            {"sesion_id": st.session_state.sesion_id, "accion_id": accion["id"], "confirmar": confirmar},
        )
    if datos:
        guardar_respuesta(datos)


iniciar_estado()

# --- Barra lateral: explicación, ejemplos y reinicio ---
with st.sidebar:
    st.header("🛡️ Agente de pólizas")
    st.caption(
        "Pregunta en español por las pólizas (datos reales de la API) o por las condiciones "
        "generales del seguro (PDF). Renovar o cancelar siempre pide tu confirmación."
    )
    st.subheader("Prueba con")
    for ejemplo in EJEMPLOS:
        if st.button(ejemplo, width="stretch"):
            st.session_state.ejemplo = ejemplo
    st.divider()
    if st.button("🗑️ Nueva conversación", width="stretch"):
        for clave in ("sesion_id", "mensajes", "pendiente", "error"):
            del st.session_state[clave]
        st.rerun()
    st.caption(f"Agente: {AGENTE_URL}")

st.title("Asistente de pólizas")

# --- La conversación hasta ahora ---
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["texto"])
        mostrar_herramientas(mensaje.get("herramientas", []))

# --- Acción pendiente: los botones de confirmación ---
pendiente = st.session_state.pendiente
if pendiente:
    st.warning(f"**Acción pendiente de tu confirmación:** {pendiente['descripcion']}")
    col_si, col_no = st.columns(2)
    if col_si.button("✅ Confirmar", type="primary", width="stretch"):
        resolver_pendiente(confirmar=True)
        st.rerun()
    if col_no.button("✖️ No, cancelar", width="stretch"):
        resolver_pendiente(confirmar=False)
        st.rerun()

if st.session_state.error:
    st.error(st.session_state.error)

# --- Nueva pregunta: escrita o desde un botón de ejemplo ---
pregunta = st.chat_input("Escribe tu pregunta…") or st.session_state.pop("ejemplo", None)
if pregunta:
    preguntar(pregunta)
    st.rerun()  # vuelve a dibujar todo con la respuesta nueva
