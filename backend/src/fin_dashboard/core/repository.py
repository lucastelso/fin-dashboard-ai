import asyncio
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import CursorResult
import polars as pl
from fin_dashboard.core.logger import logger

class BaseMarketRepository:
    """
    Classe Abstrata de repositório focada em performance bruta.
    Garante Injeção de Dependência da sessão assíncrona do FastAPI.
    Ela é a classe responsável por buscar dados do banco de dados e 
    retornar como DataFrame Polars. Possui o método `fetch_as_polars` 
    que executa a query SQL e retorna os resultados como um DataFrame Polars.
    Outras classes, como aquela relacionada à construção dos indicadores financeiros 
    e de machine learning, podem herdar desta classe para reutilizar o método de fetch. 
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def fetch_as_polars(
        self,
        query_sql: str,
        params: dict[str, Any] | None = None,
    ) -> pl.DataFrame:
        """
        Executa SQL parametrizado assincronamente e vetoriza o resultado 
        para a memória C/Rust do Polars evitando o gargalo do SQLAlchemy ORM.
        Recebe uma lista de tuplas (linhas) e uma lista de nomes de colunas, 
        e constrói um DataFrame Polars, de modo a se restringir aos tipos
        nativos do python (muito mais eficiente).
        """
        try:
            # 1. I/O bound
            result: CursorResult = await self.session.execute(text(query_sql), params or {})

            # 2. CPU bound
            def _rows_to_polars() -> pl.DataFrame:

                columns = list(result.keys())
                raw_rows = result.fetchall()
                if not raw_rows:
                    logger.warning("Query retornou vazia. Instanciando Polars vazio.")
                    return pl.DataFrame(schema=columns)
                pure_tuples = list(map(tuple, raw_rows))
                return pl.DataFrame(pure_tuples, schema=columns, orient="row")

            return await asyncio.to_thread(_rows_to_polars)

        except Exception:
            logger.error("Falha na extração vetorizada", exc_info=True)
            raise