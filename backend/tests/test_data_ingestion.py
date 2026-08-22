import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

os.environ["DB_HOST"] = "localhost"

import asyncio
import polars as pl
from datetime import datetime, timezone, timedelta

from fin_dashboard.core.database import engine, AsyncSessionLocal 
from fin_dashboard.core.logger import logger
from fin_dashboard.services.fetch_yahoo import fetch_yahoo_json_async
from fin_dashboard.services.db_upsert import upsert_asset_prices 
from fin_dashboard.models.market import Base

async def main():
    tickers = ["BBAS3.SA", "PETR4.SA", "VALE3.SA", "BOVA11.SA", "IVVB11.SA", "LVOL11.SA"]
    
    end_dt = datetime.now(tz=timezone.utc)
    start_dt = end_dt - timedelta(days=20) # Máximo permitido pelo Yahoo para "5m"
    
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    logger.info(f"Buscando JSON direto para {len(tickers)} ativos via httpx...")

    tasks = [fetch_yahoo_json_async(t, start_ts, end_ts) for t in tickers]
    results = await asyncio.gather(*tasks)

    all_records = []
    for record_list in results:
        if record_list:
            all_records.extend(record_list)

    # Padrão Early Return: Se falhar, encerra o script graciosamente e não toca no banco.
    if not all_records:
        logger.warning("Nenhum dado pôde ser ingerido da API direta. Abortando pipeline.")
        return

    logger.info(f"Ingestão via JSON concluída. {len(all_records)} registros encontrados.")
    logger.info("Criando DataFrame Polars a partir de Python nativo (Safe)...")
    
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
        ]).sort("data").sample(25)
    )

    logger.info("Criando tabelas no banco de dados (se não existirem)...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Iniciando transação de persistência assíncrona...")
    async with AsyncSessionLocal() as session:
        await upsert_asset_prices(session, master_df)
        
    logger.info("Pipeline de ingestão e persistência concluída com sucesso.")   
    
if __name__ == "__main__":
    asyncio.run(main())