import sys 
import polars as pl
import numpy as np
from typing import Any, Dict, List, Union
from datetime import datetime

sys.path.append("backend")
from core.repository import BaseMarketRepository
from core.logger import logger
from services.scheduler import TICKERS_B3


class IndicadoresAnaliticos(BaseMarketRepository):
    """
    Repositório com os métodos relacionados ao Analytics de ativos financeiros.
    Otimizado para municiar Single Page Applications (React) com dados vetorizados.
    """
    ATIVOS_B3 = TICKERS_B3

    async def get_resumo_mercado(self, dt_inicio: str, dt_fim: str) -> Dict[str, Any]:
        """
        Alimenta a "Tabela de Ativos" do Dashboard.
        Retorna a variação (rentabilidade) de TODOS os ativos no período especificado.
        Faz apenas UMA leitura do banco de dados (Altíssima Performance).
        """
        query = """
            SELECT 
                p.ativo,
                q.date as data,
                q.close as fechamento
            FROM dim_ativos as p
            INNER JOIN series_ativos as q
                ON p.id_dim_ativo = q.id_dim_ativo
            WHERE q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
        """
        data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
        data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

        df = await self.fetch_as_polars(
            query, 
            params={
                'dt_inicio': data_start, 
                'dt_fim': data_end
                }
            )

        if df.is_empty():
            return {"dados": []}

        # ORDENA E AGRUPA NO POLARS
        df = df.sort(["ativo", "data"])

        # FEATURE ENGINEERING VETORIZADA: Pega o primeiro e o último preço do período filtrado
        resumo = df.group_by("ativo").agg([
            pl.col("fechamento").first().alias("preco_inicial"),
            pl.col("fechamento").last().alias("preco_final"),
            # Variação Percentual: ((Preço Final / Preço Inicial) - 1) * 100
            (((pl.col("fechamento").cast(pl.Float64).last() / pl.col("fechamento").cast(pl.Float64).first()) - 1) * 100).round(2).alias("variacao_percentual")
        ])

        # Ordena pelos que mais subiram no período
        resumo = resumo.sort("variacao_percentual", descending=True)

        return {"dados": resumo.to_dicts()}

    async def get_serie_temporal_features(
        self, dt_inicio: str, dt_fim: str, ativos: Union[str, List[str]], janela: int = 5
    ) -> Dict[str, Any]:
        """
        Alimenta o "Gráfico Principal" do Dashboard.
        Recebe UM ou MAIS ativos (lista) e devolve a série cronológica com os 
        indicadores matemáticos (EMA, Volatilidade, Retornos) já calculados.
        """
        # Trata o input para ser sempre uma lista, mesmo se receber uma string
        if isinstance(ativos, str):
            ativos = [ativos]

        # No asyncpg, precisamos usar = ANY(:ativos) em vez de IN para listas de strings
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
            query, 
            params={'dt_inicio': data_start, 'dt_fim': data_end, 'ativos': ativos}
        )

        if df.is_empty():
            return {"dados": []}

        # ORDENAÇÃO POR ATIVO E DATA
        df = df.sort(["ativo", "data"])

        # FEATURE ENGINEERING COM OVER()
        # Como podemos ter vários ativos no mesmo DataFrame (ex: PETR4 e VALE3),
        # usamos o .over("ativo") para garantir que o Polars não misture a média
        # da Petrobras com o preço da Vale.
        df = df.with_columns([
            
            # Média Móvel (MA)
            (pl.col("fechamento").rolling_mean(window_size=janela).over("ativo").alias(f"ma_{janela}")).round(2),

            # Média Móvel Exponencial (EMA)
            pl.col("fechamento").ewm_mean(span=janela, adjust=False).over("ativo").alias(f"ema_{janela}").round(2),
            
            # Retorno Logarítmico (ln(Pt / Pt-1))
            (pl.col("fechamento").log() - pl.col("fechamento").shift(1).over("ativo").log()).alias("log_return")            
        ])

        # Pipeline Secundário: Volatilidade
        # Como são dados de 5 minutos, a anualização muda. Usamos a janela como base para não complicar.
        df = df.with_columns([
            pl.col("log_return").rolling_std(window_size=janela).over("ativo").alias(f"volatilidade_{janela}")
        ])


        df_limpo = df.drop_nulls(subset=[f"ema_{janela}", f"volatilidade_{janela}"])
        df_limpo = df_limpo.with_columns(pl.col("data").dt.to_string("%Y-%m-%d %H:%M:%S"))

        return {"dados": df_limpo.to_dicts()}

    async def get_features_ml(self, dt_inicio: str, dt_fim: str, ativos: List[str]) -> Dict[str, Any]:
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