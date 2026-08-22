import asyncio
import sys
import polars as pl

sys.path.append("src")

from core.database import AsyncSessionLocal
from core.logger import logger 
from core.repository import BaseMarketRepository

class TesteFetchBD(BaseMarketRepository):
    """Classe para testar as query assincronas no banco de dados"""
    async def fetch_data(self) -> pl.DataFrame:
        query = """
            SELECT 
                p.id_dim_ativo,
                p.ativo, 
                q.date,  
                q.open, 
                q.close, 
                q.volume,
                q.atualizado_em
            FROM dim_ativos as p
            INNER JOIN series_ativos as q
                ON p.id_dim_ativo = q.id_dim_ativo
            ORDER BY q.date DESC
        """

        df = await self.fetch_as_polars(query)
        return df

async def main():
    logger.info("Iniciando teste de conexão com o banco de dados...")
    try:
        async with AsyncSessionLocal() as session:
            repo = TesteFetchBD(session=session)
            df = await repo.fetch_data()
            logger.info("Dados extraídos com sucesso.")
            print(df)
            
    except Exception as e:
        logger.error(f"Erro ao realizar fetch de dados: {e}")
    finally:
        logger.info("Teste de conexão com o banco de dados finalizado.")

if __name__ == "__main__":
    asyncio.run(main())