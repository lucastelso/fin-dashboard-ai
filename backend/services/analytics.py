import sys 
import polars as pl
import numpy as np
from typing import Any, Dict
from datetime import datetime

sys.path.append("backend")
from core.repository import BaseMarketRepository
from core.logger import logger

class IndicadoresAnaliticos(BaseMarketRepository):
    """Repositorio com os métodos relacionados ao Analytics de ativos financeiros"""

    async def acoes_do_mercado(self, dt_inicio: str, dt_fim: str, ativo: list | str | None) -> Dict[str, Any]:
         """Seleciona todos indicadores ou iuma certa quantidade deles. Se nenhum ativo em particular for selecionado
         coleta todos os ativos (abertura e fechamento)"""
         
         
         return {}
         

    async def get_media_movel(self, dt_inicio: str, dt_fim: str, ativo: str, janela: int = 5) -> Dict[str, Any]:
            """
            Calcula a média móvel simples (SMA) via Polars.

            #### Parâmetros
            - **dt_inicio (str)**: Data de início da série 
            - **dt_fim (str)**: Data final da série
            - **ativo (str)**: Nome do ativo 

            #### Retorna
            Dicionário nativamente serializável para JSON.

            """
            query = """
                SELECT 
                    p.id_dim_ativo,
                    p.ativo,
                    q.date as data,
                    q.open as abertura,
                    q.close as fechamento
                FROM dim_ativos as p
                INNER JOIN series_ativos as q
                    ON p.id_dim_ativo = q.id_dim_ativo
                WHERE p.ativo = :ativo
                    AND q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
                ORDER BY data
            """
            data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
            data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

            df = await self.fetch_as_polars(
                query, 
                params={
                    'dt_inicio': data_start,
                    'dt_fim': data_end,
                    'ativo': ativo
                }
            )

            if df.is_empty():
                return {'ativo': ativo, 'dados': []}

            df = df.sort("data")

            # FEATURE ENGINEERING: Cria a coluna de média móvel na memória Rust
            df = df.with_columns(
                pl.col("fechamento").rolling_mean(window_size=janela).alias(f"mv_avg_{janela}")
            )

            # limpa as primeiras linhas (que ficam com valor nulo por causa da janela)
            df_limpo = df.drop_nulls(subset=[f"mv_avg_{janela}"])

            # O Polars possui um cast nativo de datas para strings ISO (ótimo para JSON)
            df_limpo = df_limpo.with_columns(pl.col("data").dt.to_string("%Y-%m-%d %H:%M:%S"))

            return {'dados': df_limpo.to_dicts()}
    

    # async def generate_financial_features(self, df: pl.DataFrame, ativo: str, price_col: str = "close") -> pl.DataFrame:
    #     """
    #     Gera retornos logarítmicos, médias móveis e 
    #     volatilidade usando expressões otimizadas.
    #     Espera um DataFrame ordenado cronologicamente.
    #     """
    #     return df.with_columns([
    #         # Retorno Logarítmico
    #         (pl.col(price_col).log() - pl.col(price_col).shift(1).log()).alias("log_return"),
            
    #         # Média Móvel Exponencial (EMA) - Sensível a choques recentes
    #         pl.col(price_col).ewm_mean(span=20, adjust=False).alias("mov_avg_exp_20"),
    #     ]).with_columns([
    #         # Volatilidade (Desvio padrão anualizado assumindo 252 dias úteis)
    #         (pl.col("log_return").rolling_std(window_size=20) * np.sqrt(252)).alias("volatility_20d")
    #     ]).drop_nulls()
        