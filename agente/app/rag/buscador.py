"""RAG (Retrieval-Augmented Generation): buscar en el PDF antes de responder.

El LLM no conoce nuestro documento. En lugar de pegarle el PDF completo en
cada pregunta, buscamos solo los fragmentos relevantes y se los entregamos.
Así responde con información real y podemos citar la página.

Cómo funciona:
1. Leemos el PDF y lo partimos en fragmentos, uno por cláusula.
2. Convertimos cada fragmento en un embedding: una lista de 384 números
   que representa su significado. Textos parecidos dan vectores parecidos.
3. Con cada pregunta, calculamos su embedding y lo comparamos con todos
   los fragmentos usando similitud coseno (1 = mismo significado, 0 = nada
   que ver). Devolvemos los más parecidos.

Todo corre en este computador: el modelo de embeddings se descarga una vez
(~220 MB) y no se llama a ningún servicio externo.
"""

import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

import numpy as np
from pypdf import PdfReader

# Una línea como "4. COBERTURAS BÁSICAS" inicia una cláusula nueva.
TITULO_CLAUSULA = re.compile(r"^\d+\.\s+[A-ZÁÉÍÓÚÑ ]+$")
PIE_DE_PAGINA = re.compile(r"^Página \d+ de \d+")
# Fragmentos más largos se parten en pedazos. Se eligió midiendo: con 700, la
# pregunta "¿cubre terremotos?" no encontraba EXCLUSIONES (su significado se
# diluía entre 9 incisos); con 250, 6 de 6 preguntas de prueba aciertan.
MAX_CARACTERES = 250
SIMILITUD_MINIMA = 0.25  # por debajo de esto, el fragmento no tiene que ver con la pregunta


@dataclass
class Fragmento:
    titulo: str
    texto: str  # el pedazo que se compara con la pregunta
    pagina: int
    clausula_completa: str = ""  # lo que se le entrega al LLM


class ModeloEmbeddings(Protocol):
    """Lo que necesitamos del modelo: convertir textos en vectores (en las pruebas usamos uno falso)."""

    def embed(self, textos: list[str]) -> Iterable[np.ndarray]: ...


def leer_paginas(ruta: Path) -> list[str]:
    return [pagina.extract_text() or "" for pagina in PdfReader(ruta).pages]


def fragmentar(paginas: list[str]) -> list[Fragmento]:
    """Parte el documento por cláusulas. Cada fragmento recuerda su título y su página."""
    fragmentos: list[Fragmento] = []
    actual: Fragmento | None = None
    for numero, texto in enumerate(paginas, start=1):
        for linea in texto.splitlines():
            linea = linea.strip()
            if not linea or PIE_DE_PAGINA.match(linea):
                continue
            if TITULO_CLAUSULA.match(linea):
                actual = Fragmento(titulo=linea, texto="", pagina=numero)
                fragmentos.append(actual)
            elif actual is not None:  # lo de antes de la primera cláusula (portada) se ignora
                actual.texto = f"{actual.texto} {linea}".strip()

    # Las cláusulas muy largas se parten por oraciones, conservando el título.
    resultado: list[Fragmento] = []
    for f in fragmentos:
        resultado.extend(_partir(f))
    return resultado


def _partir(fragmento: Fragmento) -> list[Fragmento]:
    fragmento.clausula_completa = fragmento.texto
    if len(fragmento.texto) <= MAX_CARACTERES:
        return [fragmento]
    oraciones = re.split(r"(?<=[.:])\s+", fragmento.texto)
    pedazos, actual = [], ""
    for oracion in oraciones:
        if actual and len(actual) + len(oracion) > MAX_CARACTERES:
            pedazos.append(actual)
            actual = ""
        actual = f"{actual} {oracion}".strip()
    pedazos.append(actual)
    return [Fragmento(fragmento.titulo, p, fragmento.pagina, fragmento.texto) for p in pedazos]


def normalizar(vectores: np.ndarray) -> np.ndarray:
    """Deja cada vector con largo 1. Así el producto punto ES la similitud coseno."""
    return vectores / np.linalg.norm(vectores, axis=-1, keepdims=True)


class BuscadorCondiciones:
    def __init__(self, ruta_pdf: str | Path, modelo: ModeloEmbeddings):
        self._ruta_pdf = Path(ruta_pdf)
        self._modelo = modelo
        self._fragmentos: list[Fragmento] = []
        self._matriz: np.ndarray | None = None  # una fila por fragmento
        self._candado = threading.Lock()

    def _indexar(self) -> None:
        """Lee el PDF y calcula los embeddings la primera vez que se necesitan."""
        # El candado evita que dos preguntas simultáneas indexen dos veces.
        with self._candado:
            if self._matriz is not None:
                return
            fragmentos = fragmentar(leer_paginas(self._ruta_pdf))
            # Incluimos el título en el texto: "6. EXCLUSIONES ..." ayuda a encontrarlo.
            textos = [f"{f.titulo}. {f.texto}" for f in fragmentos]
            self._matriz = normalizar(np.array(list(self._modelo.embed(textos))))
            self._fragmentos = fragmentos

    def buscar(self, pregunta: str, cantidad: int = 3) -> list[dict]:
        """Devuelve las `cantidad` cláusulas más relevantes, completas.

        Se busca con fragmentos pequeños (más precisos), pero se entrega la
        cláusula entera: si la pregunta es "¿qué no cubre?", el LLM recibe las
        9 exclusiones y no solo el pedazo que más se pareció.
        """
        self._indexar()
        vector = normalizar(np.array(next(iter(self._modelo.embed([pregunta])))))
        similitudes = self._matriz @ vector  # una similitud por fragmento, todas de una vez

        resultados: list[dict] = []
        vistas: set[str] = set()
        for i in np.argsort(similitudes)[::-1]:  # índices de mayor a menor similitud
            fragmento = self._fragmentos[i]
            if similitudes[i] < SIMILITUD_MINIMA or len(resultados) == cantidad:
                break
            if fragmento.titulo in vistas:  # esa cláusula ya está en la lista
                continue
            vistas.add(fragmento.titulo)
            resultados.append({
                "clausula": fragmento.titulo,
                "pagina": fragmento.pagina,
                "texto": fragmento.clausula_completa,
                "similitud": round(float(similitudes[i]), 3),
            })
        return resultados


def crear_buscador(ruta_pdf: str, nombre_modelo: str, cache: str) -> BuscadorCondiciones:
    return BuscadorCondiciones(ruta_pdf, _ModeloPerezoso(nombre_modelo, cache))


class _ModeloPerezoso:
    """Carga el modelo real solo cuando se usa por primera vez.

    Así el servidor arranca rápido, y las pruebas (que usan un modelo falso)
    no cargan fastembed: por eso el import va aquí adentro.
    """

    def __init__(self, nombre: str, cache: str):
        self._nombre, self._cache, self._modelo = nombre, cache, None

    def embed(self, textos: list[str]) -> Iterable[np.ndarray]:
        if self._modelo is None:
            from fastembed import TextEmbedding

            self._modelo = TextEmbedding(model_name=self._nombre, cache_dir=self._cache)
        return self._modelo.embed(textos)
