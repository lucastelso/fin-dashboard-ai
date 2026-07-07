import asyncio
import polars as pl
from datetime import datetime, timezone
import sys

sys.path.append("backend")  
from core.database import Base, engine,AsyncSessionLocal
from services.db_repository import upsert_asset_prices 
from core.logger import logger
from services.fetch_yahoo import fetch_yahoo_json_async


async def main():
    tickers = ["BBAS3.SA", "PETR4.SA", "VALE3.SA", "BOVA11.SA", "IVVB11.SA"]
    
    # Conversão de datas para Unix Timestamp (exigência da API do Yahoo)
    start_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_dt =datetime.now(tz=timezone.utc)
    
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    logger.info(f"Buscando JSON direto para {len(tickers)} ativos via httpx...")

    # Dispara as corrotinas assíncronas do httpx
    tasks = [fetch_yahoo_json_async(t, start_ts, end_ts) for t in tickers]
    results = await asyncio.gather(*tasks)

    # Achatando a lista de listas em uma única lista de dicionários nativos
    all_records = []
    for record_list in results:
        if record_list:
            all_records.extend(record_list)

    if all_records:
        logger.info(f"Ingestão via JSON concluída. {len(all_records)} registros encontrados.")
        logger.info("Criando DataFrame Polars a partir de Python nativo (Safe)...")
        
        # O Polars é extremamente rápido e seguro lendo uma lista de dicionários Python puros.
        # Zero pandas, zero C++ extensions no meio do caminho.
        master_df = pl.DataFrame(all_records).cast({
            "ticker": pl.Utf8,
            "open": pl.Decimal(10, 2),
            "high": pl.Decimal(10, 2),
            "low": pl.Decimal(10, 2),
            "close": pl.Decimal(10, 2),
            "volume": pl.Int64
            })

        
        logger.info("\n\n=============== Amostra dos Dados (API Direta) ================")
        print(
            master_df.select([
                pl.col("ticker").alias("ativo"),
                pl.col("date").alias("data").dt.strftime("%Y-%m-%d"),
                pl.col("open").alias("abertura").round(2),
                pl.col("close").alias("fechamento").round(2),
                pl.col("volume")
                ]).sort("data").sample(25))
        
    else:
        logger.warning("Nenhum dado pôde ser ingerido da API direta.")

    logger.info("Criando tabelas no banco de dados (se não existirem)...")
    
    # FASE 2 - Cria as tabelas automaticamente para testes (em prod usaremos Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Iniciando transação de persistência assíncrona...")
    async with AsyncSessionLocal() as session:
        await upsert_asset_prices(session, master_df) # type: ignore
        
    logger.info("Pipeline de ingestão e persistência concluída com sucesso.")   

if __name__ == "__main__":
    asyncio.run(main())