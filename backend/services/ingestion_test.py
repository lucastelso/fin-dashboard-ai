import asyncio
import yfinance as yf
import polars as pl
from typing import List, Optional
import sys

sys.path.append("backend")  # Adiciona o diretório backend ao sys.path para importações relativas
from core.logger import logger

async def fetch_ticker_data_async(ticker: str, start_date: str, end_date: str) -> Optional[pl.DataFrame]:
    """
    Faz o fetch dos dados de um único ticker de forma não bloqueante
    e converte a saída para um DataFrame vetorizado do Polars.
    """
    try:
        # Offload da chamada bloqueante do yfinance para uma thread separada
        df_pandas = await asyncio.to_thread(
            yf.download,
            tickers=ticker,
            start=start_date,
            end=end_date,
            progress=False
        )

        if df_pandas is None:
            logger.warning(f"Nenhum dado retornado para {ticker}")
            return None

        # O yfinance moderno retorna um MultiIndex nas colunas quando o download falha parcialmente
        # ou muda dependendo da versão. Vamos achatar as colunas e resetar o índice da Data.
        df_pandas = df_pandas.reset_index()
        
        # Se for MultiIndex (versões mais novas do yf), pegamos apenas o nível superior
        if isinstance(df_pandas.columns, tuple) or hasattr(df_pandas.columns, 'levels'):
             df_pandas.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in df_pandas.columns]
        else:
             df_pandas.columns = [col.lower() for col in df_pandas.columns]

        # Conversão zero-copy (quando possível) de Pandas para Polars
        df_polars = pl.from_pandas(df_pandas)

        # Adiciona a coluna do Ticker para normalização no banco de dados (Long Format)
        # O Polars usa expressões (pl.lit) que são altamente otimizadas
        df_polars = df_polars.with_columns(pl.lit(ticker).alias("ticker"))

        return df_polars

    except Exception as e:
        logger.error(f"Falha ao processar {ticker}: {e}")
        return None

async def main():
    # .SA é o sufixo obrigatório no Yahoo Finance para ações da B3
    tickers = ["BBAS3.SA", "PETR4.SA", "VALE3.SA", "BOVA11.SA", "IVVB11.SA"]
    start_date = "2025-01-01"
    end_date = "2026-01-01"

    logger.info(f"Iniciando ingestão concorrente para {len(tickers)} ativos...")

    # Criamos uma lista de corrotinas
    tasks = [fetch_ticker_data_async(t, start_date, end_date) for t in tickers]
    
    # Executamos todas as requisições de rede paralelamente! 
    # O tempo total será praticamente o tempo da requisição mais lenta, e não a soma de todas.
    results = await asyncio.gather(*tasks)

    # Filtramos possíveis falhas (Nones) e concatenamos verticalmente (UNION ALL no SQL)
    valid_dfs = [df for df in results if df is not None]
    
    if valid_dfs:
        master_df = pl.concat(valid_dfs)
        
        logger.info("\n=== Amostra dos Dados Ingeridos ===")
        logger.info(master_df.head())
        logger.info(f"\nTotal de registros extraídos: {master_df.height} linhas.")
        
        # Exemplo rápido da velocidade do Polars: 
        # Agrupar por ticker e calcular o preço médio de fechamento (close)
        summary = master_df.group_by("ticker").agg(
            pl.col("close").mean().alias("preco_medio_periodo")
        )
        logger.info("\n=== Preço Médio por Ativo ===")
        logger.info(summary)
        
    else:
        logger.warning("Nenhum dado pôde ser ingerido.")

if __name__ == "__main__":
    # Ponto de entrada do Event Loop
    asyncio.run(main())