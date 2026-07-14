FROM python:3.11-slim

# PYTHONUNBUFFERED=1 impede o Python de atrasar os logs (print)
# PYTHONDONTWRITEBYTECODE=1 impede a criação inútil de arquivos .pyc
ENV PYTHONUNBUFFERED=1 \  
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY . .

# Inicia servidor ASGI (Uvicorn) apontando para a instância do FastAPI.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]