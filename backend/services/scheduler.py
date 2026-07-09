# backend/services/scheduler.py
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import polars as pl
import sys

sys.path.append("backend") 

from core.logger import logger
from core.database import AsyncSessionLocal, engine
from models.market import Base
from services.fetch_yahoo import fetch_yahoo_json_async
from services.db_upsert import upsert_asset_prices

# Agendador assíncrono
scheduler = AsyncIOScheduler()

async def job_ingestao_15m():
    """
    Job que roda a cada 15 min. Puxa os dados dos últimos 7 dias 
    (margem de segurança para feriados/finais de semana) e faz o Upsert.
    """
    logger.info("[CRON] Iniciando rotina de ingestão intradiária (15m)...")
    
    tickers = ["BBAS3.SA", "PETR4.SA", "VALE3.SA", "BOVA11.SA", "IVVB11.SA", "LVOL11.SA"]
    
    # Busca sempre os últimos 7 dias para garantir que não haja buracos na base
    end_dt = datetime.now(tz=timezone.utc)
    start_dt = end_dt - timedelta(days=7)
    
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    tasks = [fetch_yahoo_json_async(t, start_ts, end_ts) for t in tickers]
    results = await asyncio.gather(*tasks)

    all_records = []
    for record_list in results:
        if record_list:
            all_records.extend(record_list)

    if not all_records:
        logger.warning("[CRON] Nenhum dado retornado. Mercado fechado ou API indisponível.")
        return

    master_df = pl.DataFrame(all_records).cast({
        "ticker": pl.Utf8,
        "open": pl.Decimal(10, 2),
        "high": pl.Decimal(10, 2),
        "low": pl.Decimal(10, 2),
        "close": pl.Decimal(10, 2),
        "volume": pl.Int64
    })
    
    # NOVA sessão para o Job, independente das rotas do FastAPI
    async with AsyncSessionLocal() as session:
        try:
            await upsert_asset_prices(session, master_df)
            logger.info(f"[CRON] Upsert concluído. {master_df.height} registros processados.")
        except Exception as e:
            logger.error(f"[CRON] Falha na persistência agendada: {e}")

def setup_scheduler():
    """
    Configura os gatilhos do Cron e acopla ao scheduler.
    """
    # Trigger configurado para:
    # - Dias da semana: Segunda a Sexta (mon-fri)
    # - Horas: 10h às 17h
    # - Minutos: A cada 15 min (0, 15, 30, 45)
    # Obs: Ajuste o fuso horário caso o relógio do Docker esteja em UTC.
    trigger = CronTrigger(
        day_of_week='mon-fri',
        hour='10-17',
        minute='*/15', 
        timezone='America/Sao_Paulo'
    )
    
    scheduler.add_job(
        job_ingestao_15m, 
        trigger=trigger, 
        id='market_ingestion_15m', 
        replace_existing=True
    )
    return scheduler