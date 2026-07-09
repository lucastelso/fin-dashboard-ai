# 1. FROM: A imagem base. 
# Usamos o 'slim' do Debian para ter um Linux minúsculo, apenas com o necessário para Python.
FROM python:3.11-slim

# 2. ENV: Define variáveis de ambiente do sistema operacional.
# PYTHONUNBUFFERED=1 impede o Python de atrasar os logs (print)
# PYTHONDONTWRITEBYTECODE=1 impede a criação inútil de arquivos .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

# 3. WORKDIR: Cria a pasta /app no Linux e diz "todos os próximos comandos serão rodados aqui dentro".
WORKDIR /app

# 4. RUN: Roda comandos shell durante a criação da imagem.
# Aqui instalamos o uv nativamente no sistema do container.
RUN pip install uv

# 5. COPY (Camada de Cache 1): Copiamos APENAS os requirements primeiro.
# Por que não copiar todo o código de uma vez? Porque se você mudar 1 linha no main.py, 
# o Docker invalidaria o cache das dependências e baixaria tudo de novo. 
COPY requirements.txt .

# 6. RUN: Instala as dependências travadas usando o poder assíncrono do UV.
# O --system diz ao UV para instalar no Python global do Linux (containers não precisam de venv).
RUN uv pip install --system -r requirements.txt

# 7. COPY (Camada de Cache 2): Agora sim, copiamos o código (que muda toda hora) para dentro do /app.
COPY . .

# 8. CMD: O comando executado quando o container "acorda" (em tempo de execução).
# Iniciamos o servidor ASGI (Uvicorn) apontando para a instância do FastAPI.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]