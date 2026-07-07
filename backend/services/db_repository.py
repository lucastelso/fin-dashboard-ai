# backend/services/db_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
import polars as pl
from core.logger import logger

from models.market import SeriesAtivos, DimensaoAtivos

async def upsert_asset_prices(session: AsyncSession, df: pl.DataFrame) -> None:
    """
    Realiza a inserção dimensional:
    1. Garante que todos os ativos existam na tabela Dimensão.
    2. Recupera o mapeamento Ticker -> ID.
    3. Substitui o Ticker pelo ID no Polars.
    4. Faz o Upsert massivo na tabela de Séries Temporais (Fato).
    """
    if df.is_empty():
        return

    try:
        # ==========================================
        # ETAPA 1: ALIMENTAR A TABELA DIMENSÃO
        # ==========================================
        # Extrai os tickers únicos do lote atual
        unique_tickers = df["ticker"].unique().to_list()
        
        # Prepara a inserção na dimensão ignorando conflitos (se o ticker já existe, nada acontece)
        dim_records = [{"ativo": ticker} for ticker in unique_tickers]
        dim_stmt = insert(DimensaoAtivos).values(dim_records)
        dim_stmt = dim_stmt.on_conflict_do_nothing(index_elements=['ativo'])
        
        await session.execute(dim_stmt)
        
        # ==========================================
        # ETAPA 2: LOOKUP DAS SURROGATE KEYS
        # ==========================================
        # Busca no banco os IDs inteiros (id_dim_ativo) correspondentes aos nossos tickers
        query = select(DimensaoAtivos.id_dim_ativo, DimensaoAtivos.ativo).where(
            DimensaoAtivos.ativo.in_(unique_tickers)
        )
        result = await session.execute(query)
        
        # Monta um dicionário de mapeamento em memória: {'PETR4.SA': 1, 'VALE3.SA': 2}
        ticker_to_id = {row.ativo: row.id_dim_ativo for row in result.all()}
        
        # ==========================================
        # ETAPA 3: TRANSFORMAÇÃO VETORIZADA NO POLARS
        # ==========================================
        # Usamos o Polars para fazer o mapeamento (Join/Replace) extremamente rápido na memória C/Rust
        # Criamos um DataFrame temporário com o dicionário de chaves
        mapping_df = pl.DataFrame({
            "ticker": list(ticker_to_id.keys()),
            "id_dim_ativo": list(ticker_to_id.values())
        })
        
        # Fazemos um Inner Join e descartamos a coluna string (ticker) que o banco não quer
        df_mapped = df.join(mapping_df, on="ticker", how="inner").drop("ticker")
        
        # Converte para dicionários nativos para o SQLAlchemy
        fact_records = df_mapped.to_dicts()

        # ==========================================
        # ETAPA 4: UPSERT NA TABELA FATO
        # ==========================================
        fact_stmt = insert(SeriesAtivos).values(fact_records)

        # Se o dado já existe (mesmo ativo no mesmo dia), atualizamos os valores financeiros
        update_dict = {
            "open": fact_stmt.excluded.open,
            "high": fact_stmt.excluded.high,
            "low": fact_stmt.excluded.low,
            "close": fact_stmt.excluded.close,
            "volume": fact_stmt.excluded.volume,
            "atualizado_em": func.now()  # Garante que saibamos quando o dado foi corrigido
        }

        # A sua UniqueConstraint agora é id_dim_ativo + date
        upsert_stmt = fact_stmt.on_conflict_do_update(
            index_elements=['id_dim_ativo', 'date'],
            set_=update_dict
        )

        await session.execute(upsert_stmt)
        
        # O Commit consolida a inserção na dimensão e na fato ao mesmo tempo (ACID)
        await session.commit()
        logger.info(f"Sucesso: {len(fact_records)} registros na Fato e {len(unique_tickers)} ativos mapeados.")

    except Exception as e:
        # Se qualquer coisa falhar, nada é salvo (evita inconsistência relacional)
        await session.rollback()
        logger.error(f"Erro transacional ao salvar no banco: {e}")
        raise e