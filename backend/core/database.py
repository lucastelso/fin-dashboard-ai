# backend/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.engine import URL 
from dotenv import load_dotenv
import sys
import os

sys.path.append("backend")

from core.logger import logger

load_dotenv(dotenv_path=".env")

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST", "postgres_db")  # Nome do serviço no docker-compose.yml

def is_running_in_docker() -> bool:
    return os.path.exists('/.dockerenv')

# if is_running_in_docker():
#     DB_HOST = "postgres_db" 
# else:
#     DB_HOST = "127.0.0.1"

DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)

logger.debug(f"\nREDE: Rodando no Docker? {is_running_in_docker()}")


# Usa o método render_as_string com hide_password para debugar em segurança
logger.debug(f"REDE: Conectando em: {DATABASE_URL.render_as_string(hide_password=True)}\n")

# Motor do banco do proteções de I/O
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    pool_size=10, 
    max_overflow=20,
    pool_pre_ping=True, # Verifica se a conexão caiu (ex: reinício do banco) antes de usá-la
    connect_args={
        # Timeout para estabelecer a conexão com o banco (se ele cair, falha rápido em vez de travar)
        "timeout": 10.0, 
        
        # O "Kill Switch" para queries analíticas pesadas. 
        # Nenhuma transação pode passar de 60 segundos. 
        # Acima disso, o asyncpg cancela a operação e libera o worker do FastAPI.
        "command_timeout": 60.0 
    }
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()