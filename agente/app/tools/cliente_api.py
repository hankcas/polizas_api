"""Cliente HTTP para la API de pólizas (Spring Boot desplegada en Render).

Aquí vive todo lo que tiene que ver con hablar con la API:
la API key, los timeouts, los reintentos y la traducción de errores HTTP
a mensajes que una persona entiende.
"""

import logging
import time
from collections.abc import Callable
from typing import Any

import httpx

from app.config import Settings

log = logging.getLogger(__name__)

# Códigos con los que vale la pena volver a intentar: el servidor está
# despertando o saturado, no es que la petición esté mal.
CODIGOS_REINTENTABLES = {502, 503, 504}


class ErrorApiPolizas(Exception):
    """Error de la API con un mensaje que se le puede mostrar al usuario."""


class ApiKeyInvalida(ErrorApiPolizas):
    """La API respondió 401: la API key del .env es incorrecta."""


class ApiNoDisponible(ErrorApiPolizas):
    """La API no respondió después de todos los intentos."""


class ClienteApiPolizas:
    def __init__(
        self,
        settings: Settings,
        http: httpx.Client | None = None,
        esperar: Callable[[float], None] = time.sleep,
    ):
        # `http` y `esperar` se pueden reemplazar en las pruebas: así probamos
        # los reintentos sin red real y sin esperar segundos de verdad.
        self._intentos = settings.polizas_api_intentos
        self._esperar = esperar
        self._http = http or httpx.Client(
            base_url=settings.polizas_api_url,
            headers={"x-api-key": settings.polizas_api_key.get_secret_value()},
            timeout=settings.polizas_api_timeout,
        )

    def listar_polizas(self, tipo: str | None = None, estado: str | None = None) -> list[dict]:
        # Solo mandamos los filtros que tienen valor: GET /polizas?tipo=COLECTIVA
        filtros = {"tipo": tipo, "estado": estado}
        params = {clave: valor for clave, valor in filtros.items() if valor}
        return self._pedir("GET", "/polizas", params=params)

    def _pedir(self, metodo: str, ruta: str, **kwargs: Any) -> Any:
        for intento in range(1, self._intentos + 1):
            try:
                respuesta = self._http.request(metodo, ruta, **kwargs)
            except (httpx.TimeoutException, httpx.ConnectError) as error:
                motivo = f"no respondió ({type(error).__name__})"
            else:
                # `else` corre solo si no hubo excepción: sí hubo respuesta HTTP.
                if respuesta.status_code not in CODIGOS_REINTENTABLES:
                    return self._procesar(respuesta)
                motivo = f"respondió HTTP {respuesta.status_code}"

            if intento < self._intentos:
                espera = 2**intento  # 2, 4, 8 segundos: cada vez esperamos más
                log.warning(
                    "La API de pólizas %s (intento %d de %d). Puede estar despertando; "
                    "reintento en %d s.",
                    motivo, intento, self._intentos, espera,
                )
                self._esperar(espera)

        raise ApiNoDisponible(
            f"La API de pólizas no respondió después de {self._intentos} intentos. "
            "Está en el plan gratuito de Render y puede tardar en despertar: "
            "espera un minuto y vuelve a preguntar."
        )

    @staticmethod
    def _procesar(respuesta: httpx.Response) -> Any:
        if respuesta.status_code == 401:
            # No reintentamos: con la misma clave fallaría igual.
            raise ApiKeyInvalida(
                "La API rechazó la API key (401). Revisa POLIZAS_API_KEY en el archivo .env."
            )
        if respuesta.is_error:
            # La API devuelve sus errores con un campo "mensaje"
            # (ej. "No se puede renovar una póliza cancelada").
            try:
                mensaje = respuesta.json().get("mensaje")
            except ValueError:
                mensaje = None
            raise ErrorApiPolizas(mensaje or f"La API respondió con error HTTP {respuesta.status_code}.")
        return respuesta.json()
