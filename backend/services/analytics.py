import sys 
import polars as pl
from typing import Any, Dict
from datetime import datetime

sys.path.append("backend")
from core.repository import BaseMarketRepository
from core.logger import logger

class IndicadoresAnaliticos(BaseMarketRepository):
    """Repositorio com os métodos relacionados ao Analytics de ativos financeiros"""

    async def get_media_movel(self, dt_inicio: str, dt_fim: str, ativo: str, janela: int = 5) -> Dict[str, Any]:
            """
            Calcula a média móvel simples (SMA) via Polars.
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

            # ORDENAÇÃO
            df = df.sort("data")

            # FEATURE ENGINEERING: Cria a coluna de média móvel na memória Rust
            df = df.with_columns(
                pl.col("fechamento").rolling_mean(window_size=janela).alias(f"sma_{janela}")
            )

            # limpa as primeiras linhas (que ficam com valor nulo por causa da janela)
            df_limpo = df.drop_nulls(subset=[f"sma_{janela}"])

            # O Polars possui um cast nativo de datas para strings ISO (ótimo para JSON)
            df_limpo = df_limpo.with_columns(pl.col("data").dt.to_string("%Y-%m-%d %H:%M:%S"))

            return {'ativo': ativo, 'dados': df_limpo.to_dicts()}
            