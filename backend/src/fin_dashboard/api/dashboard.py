from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import date
import asyncio


from fin_dashboard.core.database import get_db
from fin_dashboard.core.logger import logger
from fin_dashboard.services.analytics import IndicadoresAnaliticos
from fin_dashboard.services.ml import executar_pipeline_kmeans
from fin_dashboard.services.macro_eco import MacroeconomiaAPI
from fin_dashboard.services.llm import AnalistaQualitativo
from fin_dashboard.schemas.market import (
    APIResponse,
    Resumo, Series, MLClusteringResult, 
    KPIsMAcro, AnaliseQualitativa
)


router = APIRouter(
    prefix="/dashboard-ativos", 
    tags=['Analytics & Dashboard']
)
@router.get("/resumo", response_model=APIResponse[Resumo])
async def resumo_mercado(
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=[date.today()]),
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


@router.get("/series", response_model=APIResponse[Series])
async def serie_temporal_ativos(
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=[date.today()]),
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
    

@router.get("/kpis-macro", response_model=APIResponse[KPIsMAcro])
async def kpis_macroeconomicos() -> Dict[str, Any]:
    """
    ALIMENTA OS DADOS MACROECONOMICOS:
    Dados macroeconômicos que ficam no topo da tela (IPCA e SELIC)
    """
    try:
        dados = await MacroeconomiaAPI.get_kpis_gerais()
        return dados
    except Exception as e:
        logger.error(f"Erro no endpoint dos KPIs macroeconomicos: {e}")
        # Em vez de estourar erro 500 e quebrar a UI, retorna zeros de fallback
        return {"selic": 0.0, "ipca": 0.0}

@router.get("/machine-learning", response_model=MLClusteringResult)
async def analise_avancada_ml(
    request: Request,
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=[date.today()]),
    ativos: Optional[List[str]] = Query(None, description="Tickers para clusterização. Vazio = Todos", alias="ativos"),
    n_clusters: int = Query(4, description="Quantidade de grupos desejada"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint de Machine Learning (Heavy Compute).
    """
    try:
        lista_ativos = ativos if ativos else IndicadoresAnaliticos.ATIVOS_B3

        analyzer = IndicadoresAnaliticos(session)
        matriz_retornos = await analyzer.get_features_ml(
            dt_inicio=dt_inicio, dt_fim=dt_fim, ativos=lista_ativos
        )
        
        if not matriz_retornos:
            raise HTTPException(status_code=404, detail="Sem dados suficientes para análise.")

        loop = asyncio.get_running_loop()
        pool = request.app.state.process_pool 
        
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
    

@router.get("/analise-qualitativa", response_model=AnaliseQualitativa)
async def analise_qualitativa_ia(
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=[date.today()]),
    ativos: List[str] = Query(None, description="Tickers alvo", alias="ativos"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Retorna um texto (Markdown) gerado por IA (Gemini) explicando os motivos 
    macroeconômicos por trás dos números do período.
    """
    try:
        lista_ativos = ativos if ativos else IndicadoresAnaliticos.ATIVOS_B3
        analyzer = IndicadoresAnaliticos(session)
        
        dados_quantitativos = await analyzer.get_features_ml(dt_inicio, dt_fim, lista_ativos)
        features_2d = dados_quantitativos.get("features_2d", [])
        
        kpis_macro = await MacroeconomiaAPI.get_kpis_gerais()

        ia_service = AnalistaQualitativo()
        loop = asyncio.get_running_loop()
        
        sintese = await loop.run_in_executor(
            None, 
            ia_service.gerar_sintese, 
            dt_inicio, 
            dt_fim, 
            features_2d, 
            kpis_macro,
            lista_ativos
        )
        
        return {"texto_analise": sintese}

    except Exception as e:
        logger.error(f"Erro no endpoint /analise-qualitativa: {e}")
        raise HTTPException(status_code=500, detail="Falha ao gerar síntese da IA.")