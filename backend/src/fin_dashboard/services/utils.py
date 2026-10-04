import polars as pl
from typing import Any, Dict, List

def _processar_resumo_mercado_cpu(df: pl.DataFrame) -> List[Dict[str, Any]]:
    """CPU-Bound: Processa a rentabilidade global do mercado."""
    if df.is_empty():
        return []

    df = df.sort(["ativo", "data"])

    resumo = df.group_by("ativo").agg([
        pl.col("fechamento").first().alias("preco_inicial"),
        pl.col("fechamento").last().alias("preco_final"),
        (((pl.col("fechamento").last() / pl.col("fechamento").first()) - 1) * 100).alias("variacao_percentual")
    ])

    resumo = resumo.sort("variacao_percentual", descending=True)
    return resumo.to_dicts()

def _processar_serie_temporal_cpu(df: pl.DataFrame, janela: int, rule: str | None) -> List[Dict[str, Any]]:
    """CPU-Bound: Aplica downsampling dinâmico e calcula indicadores técnicos."""
    if df.is_empty():
        return []

    df = df.sort(["ativo", "data"])


    if rule:
        df = df.group_by_dynamic(
            "data", 
            every=rule, 
            by="ativo" 
        ).agg([
            pl.col("fechamento").last().alias("fechamento")
        ])
        df = df.sort(["ativo", "data"])

    janela_segura = min(janela, df.height)
    if janela_segura < 2: 
        janela_segura = 2 

    df = df.with_columns([
        pl.col("fechamento").rolling_mean(window_size=janela_segura).over("ativo").alias("ma"),
        pl.col("fechamento").ewm_mean(span=janela_segura, adjust=False).over("ativo").alias("ema"),
        (pl.col("fechamento").log() - pl.col("fechamento").shift(1).over("ativo").log()).alias("log_return")            
    ])

    df = df.with_columns([
        pl.col("log_return").rolling_std(window_size=janela_segura).over("ativo").alias("volatilidade")
    ])


    df_limpo = df.fill_null(strategy="forward").fill_null(0.0)
    
    if df_limpo.height == 0:
        return []

    df_limpo = df_limpo.with_columns(pl.col("data").dt.to_string("%Y-%m-%d %H:%M:%S"))
    return df_limpo.to_dicts()

def _processar_features_ml_cpu(df: pl.DataFrame) -> Dict[str, Any]:
    """CPU-Bound: Prepara a matriz matemática para o algoritmo K-Means."""
    if df.is_empty():
        return {"features_2d": []}

    df = df.sort(["ativo", "data"])
    
    df = df.with_columns(
        (pl.col("fechamento").log() - pl.col("fechamento").shift(1).over("ativo").log()).alias("log_return")
    ).drop_nulls()

    features_df = df.group_by("ativo").agg([
        (pl.col("log_return").sum() * 100).alias("retorno_acumulado"),
        (pl.col("log_return").std() * 100).alias("volatilidade")
    ])

    return {
        "features_2d": features_df.to_dicts()
    }