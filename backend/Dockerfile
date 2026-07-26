FROM python:3.11-slim


ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Força o uv a usar o python do sistema do contêiner
    UV_SYSTEM_PYTHON=1 

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt .

# Usa o cache de build do DockerKit para o UV. 
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip sync requirements.txt

# Criação de usuário sem privilégios
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# Copia o restante do código e ajusta as permissões para o novo usuário
COPY --chown=appuser:appgroup . .

# Faz o drop de privilégios de root para o usuário seguro
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]p