"""Configuración del proyecto, leída de variables de entorno o del archivo .env.

Ningún secreto vive en el código: todo sale de aquí.
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Le dice a pydantic que lea el archivo .env e ignore variables que no conoce.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API de pólizas. Cada atributo corresponde a una variable del .env
    # (POLIZAS_API_URL -> polizas_api_url; mayúsculas o minúsculas da igual).
    polizas_api_url: str = "https://polizas-api-g8ew.onrender.com"
    polizas_api_key: SecretStr  # sin valor por defecto: es obligatoria
    polizas_api_timeout: float = 30.0
    polizas_api_intentos: int = 5

    # Modelo de lenguaje
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3.5-flash"
    gemini_api_key: SecretStr | None = None


@lru_cache  # lee el .env una sola vez y reutiliza el resultado
def get_settings() -> Settings:
    return Settings()
