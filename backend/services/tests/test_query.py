import asyncio
import sys
import polars as pl

sys.path.append("backend")
from core.database import engine
from core.logger import logger 

async def fetch_data() -> pl.DataFrame:
    query = """
    
    SELECT 
        p.id_dim_ativo,
        p.ativo, 
        q.date,  
        q.open, 
        q.close, 
        q.volume
    FROM dim_ativos as p
    INNER JOIN series_ativos as q
        ON p.id_dim_ativo = q.id_dim_ativo
    LIMIT 10

    """
    df = await asyncio.to_thread(pl.read_database, query=query, connection=engine)
    return df

async def main():
    logger.info("Iniciando teste de conexão com o banco de dados...")
    try:
        df = await fetch_data()
        print(df.head())
    except Exception as e:
        logger.error(f"Erro ao fetch dados: {e}")
    finally:
        logger.info("Teste de conexão com o banco de dados finalizado.")

if __name__ == "__main__":
    asyncio.run(main())