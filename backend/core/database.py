import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

sys.path.append("backend")

from core.config import settings
from core.logger import logger

logger.debug(f"Conectando em: {settings.async_database_url.render_as_string(hide_password=True)}")

engine = create_async_engine(
    settings.async_database_url, 
    echo=False, 
    pool_size=10, 
    max_overflow=20,
    pool_pre_ping=True, 
    connect_args={
        "timeout": 10.0, 
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