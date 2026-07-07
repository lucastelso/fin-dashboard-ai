# backend/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

# Formato: postgresql+asyncpg://usuario:senha@host:porta/banco
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL não foi encontrada no ambiente.")

# A engine é a fábrica de conexões. 
# echo=False para não poluir o terminal, pool_size garante reuso de conexões.
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)

# O Session local é o que usaremos para transações atômicas
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# A classe Base de onde nossos modelos vão herdar
Base = declarative_base()

# Dependência para injeção no FastAPI futuramente
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session