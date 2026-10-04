# ESTÁGIO 1: BUILDER
FROM python:3.12-slim-bookworm AS builder 

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./


RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copia o código da aplicação
COPY . .

# Instala apenas o código da própria aplicação no ambiente virtual
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
    
# ESTÁGIO 2: RUNTIME (Produção)
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    TZ=America/Sao_Paulo

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

# Configuração de usuário seguro (Non-root)
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# Copia o venv isolado
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copia o código da aplicação
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

# Executa pelo Uvicorn usando as variáveis ativadas
CMD ["uvicorn", "fin_dashboard.main:app", "--host", "0.0.0.0", "--port", "8000"]