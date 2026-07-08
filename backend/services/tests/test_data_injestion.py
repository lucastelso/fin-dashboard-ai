import asyncio
import polars as pl
from datetime import datetime, timezone
import sys

sys.path.append("backend")  

from core.database import engine, AsyncSessionLocal  # <-- Removi o Base daqui
from services.db_upsert import upsert_asset_prices 
from core.logger import logger
from services.fetch_yahoo import fetch_yahoo_json_async
from models.market import Base

async def main():
    tickers = ["BBAS3.SA", "PETR4.SA", "VALE3.SA", "BOVA11.SA", "IVVB11.SA", "LVOL11.SA"]
    
    start_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_dt = datetime.now(tz=timezone.utc)
    
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

    # ==========================================
    # FASE 2: PERSISTÊNCIA BINDADA AO SUCESSO
    # ==========================================
    logger.info("Criando tabelas no banco de dados (se não existirem)...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Iniciando transação de persistência assíncrona...")
    async with AsyncSessionLocal() as session:
        await upsert_asset_prices(session, master_df)
        
    logger.info("Pipeline de ingestão e persistência concluída com sucesso.")   
    
if __name__ == "__main__":
    asyncio.run(main())