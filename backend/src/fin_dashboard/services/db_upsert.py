from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
import polars as pl
from datetime import datetime
from zoneinfo import ZoneInfo

from fin_dashboard.models.market import SeriesAtivos, DimensaoAtivos
from fin_dashboard.core.logger import logger

async def upsert_asset_prices(session: AsyncSession, df: pl.DataFrame) -> None:
    """
    Realiza a inserção dimensional e o upsert de séries temporais.
    NOTA: O controle transacional (commit/rollback) DEVE ser feito pelo chamador (caller),
    garantindo o padrão Unit of Work.
    """
    if df.is_empty():
        return

    # ETAPA 1: ALIMENTAR A TABELA DIMENSÃO
    unique_tickers = df["ticker"].unique().to_list()
    
    dim_records = [{"ativo": ticker} for ticker in unique_tickers]
    dim_stmt = insert(DimensaoAtivos).values(dim_records)
    dim_stmt = dim_stmt.on_conflict_do_nothing(index_elements=['ativo'])
    
    await session.execute(dim_stmt)
    
    # ETAPA 2: LOOKUP DAS SURROGATE KEYS
    query = select(DimensaoAtivos.id_dim_ativo, DimensaoAtivos.ativo).where(
        DimensaoAtivos.ativo.in_(unique_tickers)
    )
    result = await session.execute(query)
    
    ticker_to_id = {row.ativo: row.id_dim_ativo for row in result.all()}
    
    # ETAPA 3: TRANSFORMAÇÃO VETORIZADA NO POLARS
    mapping_df = pl.DataFrame({
        "ticker": list(ticker_to_id.keys()),
        "id_dim_ativo": list(ticker_to_id.values())
    })
    
    df_mapped = df.join(mapping_df, on="ticker", how="inner").drop("ticker")
    
    # ETAPA 4: UPSERT NA TABELA FATO EM BATCHES
    batch_size = 1000
    
    # O uso do iter_slices() é excelente. Apenas garantimos que a conversão para
    # dict nativo (que é custosa em memória) só ocorra fragmentada.
    for batch_df in df_mapped.iter_slices(batch_size):
        
        fact_records = batch_df.to_dicts()
        fact_stmt = insert(SeriesAtivos).values(fact_records)
        
        update_dict = {
            "open": fact_stmt.excluded.open,
            "high": fact_stmt.excluded.high,
            "low": fact_stmt.excluded.low,
            "close": fact_stmt.excluded.close,
            "volume": fact_stmt.excluded.volume,
            "atualizado_em": datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
        }

        upsert_stmt = fact_stmt.on_conflict_do_update(
            index_elements=['id_dim_ativo', 'date'],
            set_=update_dict
        )

        await session.execute(upsert_stmt)
    
    logger.info(f"Processamento concluído: {df.height} registros enfileirados para a transação.")