# backend/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.engine import URL 
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")

def is_running_in_docker() -> bool:
    return os.path.exists('/.dockerenv')

if is_running_in_docker():
    DB_HOST = "postgres_db" 
else:
    DB_HOST = "127.0.0.1"

DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT, # type: ignore
    database=DB_NAME
)

print(f"\n[DEBUG DE REDE] Rodando no Docker? {is_running_in_docker()}")

# Usa o método render_as_string com hide_password para debugar em segurança
print(f"[DEBUG DE REDE] Conectando em: {DATABASE_URL.render_as_string(hide_password=True)}\n")

# Passamos a URL construída (que não é mais uma string pura, mas um objeto URL)
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session