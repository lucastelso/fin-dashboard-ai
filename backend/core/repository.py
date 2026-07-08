import asyncio
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import polars as pl
from core.logger import logger

class BaseMarketRepository:
    """
    Classe Abstrata de repositório focada em performance bruta.
    Garante Injeção de Dependência da sessão assíncrona do FastAPI.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def fetch_as_polars(self, query_sql: str, params: dict[str, Any] | None = None) -> pl.DataFrame:
        """
        Executa SQL parametrizado assincronamente e vetoriza o resultado 
        para a memória C/Rust do Polars evitando o gargalo do SQLAlchemy ORM.
        """
        try:
            # 1. I/O Bound: Requisição de rede 100% não-bloqueante
            result = await self.session.execute(text(query_sql), params or {})
            
            columns = list(result.keys())
            raw_rows = result.fetchall()

            if not raw_rows:
                logger.warning("Query retornou vazia. Instanciando Polars vazio.")
                return pl.DataFrame(schema=columns)

            # 2. CPU Bound: Isolamento térmico da thread principal
            def _build_dataframe(rows, cols):
                pure_tuples = list(map(tuple, rows))
                return pl.DataFrame(pure_tuples, schema=cols, orient="row")

            df = await asyncio.to_thread(_build_dataframe, raw_rows, columns)
            return df
            
        except Exception as e:
            logger.error(f"Falha na extração vetorizada: {e}")
            raise e