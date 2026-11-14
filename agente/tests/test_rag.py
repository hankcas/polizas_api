"""Pruebas del RAG: fragmentación, búsqueda y una evaluación de calidad con el modelo real."""

from pathlib import Path

import numpy as np
import pytest

from app.rag import buscador as rag
from app.rag.buscador import BuscadorCondiciones, fragmentar, leer_paginas

PDF = Path(__file__).resolve().parent.parent / "data" / "condiciones_generales.pdf"

PAGINAS = [
    "TÍTULO DEL DOCUMENTO\n1. COBERTURAS\nCubre el canon de arrendamiento.\n"
    "Página 1 de 2 - Documento ficticio",
    "2. EXCLUSIONES\nNo cubre terremotos.\nNo cubre multas.",
]


def test_fragmentar_por_clausulas_ignorando_portada_y_pie():
    fragmentos = fragmentar(PAGINAS)

    assert [(f.titulo, f.pagina) for f in fragmentos] == [("1. COBERTURAS", 1), ("2. EXCLUSIONES", 2)]
    assert fragmentos[0].texto == "Cubre el canon de arrendamiento."  # sin la portada ni el pie
    assert fragmentos[1].texto == "No cubre terremotos. No cubre multas."  # líneas unidas


def test_clausula_larga_se_parte_pero_guarda_el_texto_completo(monkeypatch):
    monkeypatch.setattr(rag, "MAX_CARACTERES", 25)

    fragmentos = fragmentar(PAGINAS)
    exclusiones = [f for f in fragmentos if f.titulo == "2. EXCLUSIONES"]

    assert [f.texto for f in exclusiones] == ["No cubre terremotos.", "No cubre multas."]
    assert all(f.clausula_completa == "No cubre terremotos. No cubre multas." for f in exclusiones)


def test_el_pdf_de_ejemplo_tiene_14_clausulas():
    titulos = {f.titulo for f in fragmentar(leer_paginas(PDF))}
    assert len(titulos) == 14


class EmbeddingsDePalabras:
    """Modelo falso: un vector que cuenta palabras clave. Suficiente para probar la búsqueda."""

    PALABRAS = ["canon", "terremotos", "multas", "cubre"]

    def embed(self, textos):
        for texto in textos:
            texto = texto.lower()
            yield np.array([texto.count(p) + 0.01 for p in self.PALABRAS], dtype=float)


def buscador_falso(tmp_path, monkeypatch, paginas=PAGINAS) -> BuscadorCondiciones:
    monkeypatch.setattr(rag, "leer_paginas", lambda ruta: paginas)
    return BuscadorCondiciones(tmp_path / "no-importa.pdf", EmbeddingsDePalabras())


def test_buscar_devuelve_la_clausula_mas_parecida_primero(tmp_path, monkeypatch):
    resultados = buscador_falso(tmp_path, monkeypatch).buscar("¿terremotos?")

    # COBERTURAS no habla de terremotos: queda bajo la similitud mínima y no aparece.
    assert [r["clausula"] for r in resultados] == ["2. EXCLUSIONES"]
    assert resultados[0]["pagina"] == 2


def test_no_repite_clausulas_y_entrega_la_completa(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "MAX_CARACTERES", 25)  # EXCLUSIONES queda en 2 pedazos

    resultados = buscador_falso(tmp_path, monkeypatch).buscar("no cubre terremotos ni multas")

    titulos = [r["clausula"] for r in resultados]
    assert titulos.count("2. EXCLUSIONES") == 1
    assert resultados[0]["texto"] == "No cubre terremotos. No cubre multas."


def test_pregunta_sin_relacion_no_devuelve_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "SIMILITUD_MINIMA", 0.99)
    assert buscador_falso(tmp_path, monkeypatch).buscar("capital de Francia") == []


# --- Evaluación con el modelo real (se corre con: pytest -m lento) ---

PREGUNTAS_DE_EVALUACION = [
    ("¿Qué no cubre el seguro?", "6."),
    ("¿Cubre daños por un terremoto?", "6."),
    ("¿Cómo sube el precio al renovar?", "8."),
    ("¿Cuánto tiempo tengo para avisar que el inquilino no pagó?", "11."),
    ("¿Me devuelven plata si cancelo?", "9."),
    ("¿Cuánto me descuentan de la indemnización?", "12."),
]


@pytest.mark.lento
@pytest.mark.parametrize("pregunta, clausula", PREGUNTAS_DE_EVALUACION)
def test_calidad_de_la_busqueda_con_el_modelo_real(pregunta, clausula):
    """Si se cambia el modelo o el tamaño de los fragmentos, esta prueba avisa si empeoró."""
    from app.config import Settings

    s = Settings(_env_file=None, polizas_api_key="x")
    buscador = _buscador_real(s.embeddings_modelo, s.embeddings_cache)
    encontradas = [r["clausula"] for r in buscador.buscar(pregunta)]
    assert any(c.startswith(clausula) for c in encontradas), encontradas


_CACHE: dict = {}


def _buscador_real(modelo: str, cache: str) -> BuscadorCondiciones:
    if "b" not in _CACHE:  # se crea una sola vez para las 6 preguntas
        _CACHE["b"] = rag.crear_buscador(str(PDF), modelo, cache)
    return _CACHE["b"]
