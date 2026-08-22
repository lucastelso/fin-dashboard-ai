FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Criação de usuário sem privilégios para segurança
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# AGORA, COPIAMOS TUDO (inclusive o pyproject.toml) para que o uv saiba o que construir
COPY --chown=appuser:appgroup . .

# Usamos o UV para ler o pyproject.toml e instalar todas as dependências e o pacote globalmente no sistema do contêiner
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system .

# Faz o drop de privilégios de root para o usuário seguro
USER appuser

EXPOSE 8000

CMD ["uvicorn", "fin_dashboard.main:app", "--host", "0.0.0.0", "--port", "8000"]