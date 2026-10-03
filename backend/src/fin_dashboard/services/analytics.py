import sys 
import polars as pl
import numpy as np
from typing import Any, Dict, List, Union
from datetime import datetime

from fin_dashboard.core.repository import BaseMarketRepository
from fin_dashboard.core.logger import logger
from fin_dashboard.services.scheduler import TICKERS_B3


class IndicadoresAnaliticos(BaseMarketRepository):
    """        
    Repositório com os métodos relacionados ao Analytics de ativos financeiros.
    Otimizado para municiar Single Page Applications (React) com dados vetorizados.
    """
    
    ATIVOS_B3 = TICKERS_B3

    async def get_resumo_mercado(
              self, 
              dt_inicio: str, 
              dt_fim: str
        ) -> Dict[str, Any]:
        query = """
            SELECT p.ativo, q.date as data, q.close as fechamento
            FROM dim_ativos as p
            INNER JOIN series_ativos as q ON p.id_dim_ativo = q.id_dim_ativo
            WHERE q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
        """
        data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
        data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

        df = await self.fetch_as_polars(query, params={'dt_inicio': data_start, 'dt_fim': data_end})

        if df.is_empty():
            return {"dados": []}

        df = df.sort(["ativo", "data"])

        # O casting foi removido pois a base já retorna Float64 nativo
        # O round(2) foi suprimido. A responsabilidade de arredondamento visual é do Front-end (React)
        resumo = df.group_by("ativo").agg([
            pl.col("fechamento").first().alias("preco_inicial"),
            pl.col("fechamento").last().alias("preco_final"),
            (((pl.col("fechamento").last() / pl.col("fechamento").first()) - 1) * 100).alias("variacao_percentual")
        ])

        resumo = resumo.sort("variacao_percentual", descending=True)
        return {'status': 'sucesso', "dados": resumo.to_dicts()}

    async def get_serie_temporal_features(
              self, 
              dt_inicio: str, 
              dt_fim: str, 
              ativos: Union[str, List[str]], 
              janela: int = 5
        ) -> Dict[str, Any]:
        if isinstance(ativos, str):
            ativos = [ativos]

        query = """
            SELECT p.ativo, q.date as data, q.close as fechamento
            FROM dim_ativos as p
            INNER JOIN series_ativos as q 
                ON p.id_dim_ativo = q.id_dim_ativo
            WHERE p.ativo = ANY(:ativos)
                AND q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
        """
        data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
        data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

        df = await self.fetch_as_polars(query, params={'dt_inicio': data_start, 'dt_fim': data_end, 'ativos': ativos})

        if df.is_empty():
            return {'status': 'df vazio', "dados": []}

        df = df.with_columns([
            # Média Móvel (MA)
            (pl.col("fechamento").rolling_mean(window_size=janela).over("ativo").alias("ma")),

            # Média Móvel Exponencial (EMA)
            pl.col("fechamento").ewm_mean(span=janela, adjust=False).over("ativo").alias("ema"),
            
            # Retorno Logarítmico
            (pl.col("fechamento").log() - pl.col("fechamento").shift(1).over("ativo").log()).alias("log_return")            
        ])

        # Pipeline Secundário: Volatilidade
        df = df.with_columns([
            pl.col("log_return").rolling_std(window_size=janela).over("ativo").alias("volatilidade")
        ])

        # O drop_nulls agora usa os nomes fixos também
        df_limpo = df.drop_nulls(subset=["ema", "volatilidade"])
        df_limpo = df_limpo.with_columns(pl.col("data").dt.to_string("%Y-%m-%d %H:%M:%S"))
        
        return {'status': 'sucesso', "dados": df_limpo.to_dicts()}

    async def get_features_ml(
              self, 
              dt_inicio: str, 
              dt_fim: str, 
              ativos: List[str]
        ) -> Dict[str, Any]:
            """
            Gera as Features 2D (Retorno e Risco) para o Scatterplot do K-Means
            e preserva a matriz de série temporal para a Correlação de Pearson.
            """
            query = """
                SELECT 
                    p.ativo,
                    q.date as data,
                    q.close as fechamento
                FROM dim_ativos as p
                INNER JOIN series_ativos as q
                    ON p.id_dim_ativo = q.id_dim_ativo
                WHERE p.ativo = ANY(:ativos)
                    AND q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
            """
            data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
            data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

            df = await self.fetch_as_polars(
                query, params={'dt_inicio': data_start, 'dt_fim': data_end, 'ativos': ativos}
            )

            if df.is_empty():
                return {}

            df = df.sort(["ativo", "data"])
            
            # Calcula o Retorno Logarítmico
            df = df.with_columns(
                (pl.col("fechamento").log() - pl.col("fechamento").shift(1).over("ativo").log()).alias("log_return")
            ).drop_nulls()

            # Features 2D para o K-Means (Risco x Retorno)
            features_df = df.group_by("ativo").agg([
                (pl.col("log_return").sum() * 100).round(4).alias("retorno_acumulado"),
                (pl.col("log_return").std() * 100).round(4).alias("volatilidade")
            ])

            # Matriz Dinâmica para a Correlação
            df_pivot = df.pivot(values="log_return", index="data", on="ativo").fill_null(0.0)
            
            return {
                "features_2d": features_df.to_dicts(),
                "series_temporais": df_pivot.drop("data").to_dict(as_series=False)
            }