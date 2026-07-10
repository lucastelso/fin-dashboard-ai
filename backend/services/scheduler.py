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

TICKERS_B3 = [
    "PETR4.SA", "PETR3.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBDC3.SA", 
    "BBAS3.SA", "ABEV3.SA", "WEGE3.SA", "SUZB3.SA", "ELET3.SA", "RENT3.SA", 
    "B3SA3.SA", "RADL3.SA", "JBSS3.SA", "BPAC11.SA", "EQTL3.SA", "VIVT3.SA",
    "RAIL3.SA", "SBSP3.SA", "PRIO3.SA", "CPLE6.SA", "BBSE3.SA", "GGBR4.SA",
    "UGPA3.SA", "CMIG4.SA", "CSAN3.SA", "HYPE3.SA", "ENEV3.SA", "TIMS3.SA",
    "CCRO3.SA", "TOTS3.SA", "EGIE3.SA", "KLBN11.SA", "CSNA3.SA", "ALPA4.SA",
    "BOVA11.SA", "IVVB11.SA", "LVOL11.SA", "DIVO11.SA", "SMAL11.SA"
    # Pode adicionar até 100 aqui sem medo
]

async def job_ingestao_5m():
    logger.info(f"[CRON] Iniciando rotina de ingestão para {len(TICKERS_B3)} ativos...")
    
    end_dt = datetime.now(tz=timezone.utc)
    start_dt = end_dt - timedelta(days=7)
    
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    semaforo = asyncio.Semaphore(5) # DEFINIDO PARA 5 REQUISIÇÕES HTTP POR VEZ

    async def fetch_com_semaforo(ticker):
        """
        Queremos colocar dezenas de ações ao mesmo tempo, mas o firewall do yahoo nos verá
        como um ameaça ou um ataque de DDoS se tiver 100 conexões HTTP neles de uma vez. 
        Com o código abaixo, usamos a regra do semáforo, ou seja, uma catraca para enviarmos apenas
        cinco requisições por vez, ainda de forma concorrente, mas sendo civilizados para não termos
        nosso IP bloqueado.
        """
        async with semaforo:
            # Colocamos um mini-delay de 100ms para amaciar o tráfego
            await asyncio.sleep(0.1) 
            return await fetch_yahoo_json_async(ticker, start_ts, end_ts)

    # Cria as tarefas envoltas no semáforo
    tasks = [fetch_com_semaforo(t) for t in TICKERS_B3]
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
        minute='*/5', 
        timezone='America/Sao_Paulo'
    )
    
    scheduler.add_job(
        job_ingestao_5m, 
        trigger=trigger, 
        id='market_ingestion_5m', 
        replace_existing=True
    )
    return scheduler