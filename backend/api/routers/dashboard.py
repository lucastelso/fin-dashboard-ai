# backend/api/routers/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import asyncio

from core.database import get_db
from core.logger import logger
from services.analytics import IndicadoresAnaliticos
from services.ml import executar_pipeline_kmeans

# Definição do Router Modular com o prefixo unificado
router = APIRouter(
    prefix="/dashboard-ativos", 
    tags=['Analytics & Dashboard']
)
@router.get("/resumo")
async def resumo_mercado(
    # Usamos 'examples' (plural) com uma lista para alinhar com o Pydantic V2
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=["2026-07-10"]),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    ALIMENTA A TABELA GERAL (Macro):    
    Retorna o primeiro preço, o último preço e a variação percentual de TODOS 
    os ativos da base no período selecionado, em uma única chamada de banco.
    """
    try:
        analyzer = IndicadoresAnaliticos(session)
        resultado = await analyzer.get_resumo_mercado(dt_inicio=dt_inicio, dt_fim=dt_fim)
        
        if not resultado['dados']:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado para o período filtrado.")
            
        return resultado  # Já segue o contrato {"dados": [...]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Falha crítica no endpoint /resumo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento macro dos ativos.")


@router.get("/series")
async def serie_temporal_ativos(
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=["2026-07-10"]),
    ativos: List[str] = Query(..., description="Lista de tickers para o gráfico", alias="ativos"),
    janela: int = Query(20, description="Janela de períodos para EMA/Volatilidade"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    ALIMENTA O GRÁFICO DINÂMICO (Micro):
    Retorna a série temporal cronológica com preço de fechamento, EMA 
    e volatilidade calculados via Polars para os ativos selecionados.
    """
    try:
        analyzer = IndicadoresAnaliticos(session)
        resultado = await analyzer.get_serie_temporal_features(
            dt_inicio=dt_inicio,
            dt_fim=dt_fim,
            ativos=ativos,
            janela=janela
        )
        
        if not resultado['dados']:
            raise HTTPException(status_code=404, detail="Nenhum dado disponível para o(s) ativo(s) selecionado(s).")
            
        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Falha crítica no endpoint /series: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no cálculo quantitativo da série temporal.")
    

@router.get("/machine-learning")
async def analise_avancada_ml(
    request: Request, # Acesso ao estado global da aplicação
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-06-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=["2026-07-10"]),
    ativos: List[str] = Query(..., description="Tickers para clusterização", alias="ativos"),
    n_clusters: int = Query(4, description="Quantidade de grupos desejada"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint de Machine Learning (Heavy Compute).
    Extrai retornos do Postgres/Polars e envia para processamento paralelo 
    no ProcessPoolExecutor, protegendo o Event Loop do FastAPI.
    """
    try:
        # I/O Bound: Busca dados no banco e pivota no Polars
        analyzer = IndicadoresAnaliticos(session)
        matriz_retornos = await analyzer.get_matriz_retornos(
            dt_inicio=dt_inicio, dt_fim=dt_fim, ativos=ativos
        )
        
        if not matriz_retornos:
            raise HTTPException(status_code=404, detail="Sem dados suficientes para análise.")

        # Compute Bound: Despacha para um núcleo livre da CPU
        loop = asyncio.get_running_loop()
        pool = request.app.state.process_pool
        
        # O Event Loop fica LIVRE enquanto o K-Means roda na outra thread/processo!
        resultado_ml = await loop.run_in_executor(
            pool, 
            executar_pipeline_kmeans, 
            matriz_retornos, 
            n_clusters
        )
        
        return resultado_ml

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro catastrófico no pipeline de ML: {e}")
        raise HTTPException(status_code=500, detail="Falha no modelo de Machine Learning.")