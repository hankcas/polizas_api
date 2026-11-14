# Imagen del agente de pólizas. La misma imagen sirve para los dos servicios:
# la API del agente (FastAPI, por defecto) y la interfaz (Streamlit, ver docker-compose.yml).
FROM python:3.14-slim

# Sin archivos .pyc y con los logs saliendo de inmediato.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Usuario sin privilegios: si alguien comprometiera la app, no tendría acceso de administrador.
RUN useradd --create-home agente && mkdir /app && chown agente /app
WORKDIR /app

# Primero solo las dependencias: Docker reutiliza esta capa mientras
# requirements.txt no cambie, y reconstruir es mucho más rápido.
COPY requirements.txt .
RUN pip install -r requirements.txt

USER agente

# Descargamos el modelo de embeddings al construir la imagen, no en la primera pregunta.
ARG EMBEDDINGS_MODELO=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
ENV EMBEDDINGS_MODELO=${EMBEDDINGS_MODELO} \
    EMBEDDINGS_CACHE=/app/.cache/fastembed
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='${EMBEDDINGS_MODELO}', cache_dir='${EMBEDDINGS_CACHE}')"

COPY --chown=agente app ./app
COPY --chown=agente ui ./ui
COPY --chown=agente data ./data

EXPOSE 8000 8501
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
